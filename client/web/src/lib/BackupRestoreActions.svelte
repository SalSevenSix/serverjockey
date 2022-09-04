<script>
  import { onMount, onDestroy } from 'svelte';
  import { notifyInfo, notifyError } from '$lib/notifications';
  import { humanFileSize, ReverseRollingLog } from '$lib/util';
  import { instance, serverStatus, newGetRequest, newPostRequest, rawPostRequest, SubscriptionHelper } from '$lib/serverjockeyapi';

  let subs = new SubscriptionHelper();
  let logLines = new ReverseRollingLog();
  let logText = '';
  let processing = false;
  let paths = [];
  let uploadFiles = [];

	onMount(reload);

	onDestroy(function() {
		subs.stop();
	});

	function reload() {
	  fetch($instance.url + '/backups', newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        json.sort(function(a, b) {
          return a.name.localeCompare(b.name);
        });
        json.reverse();
        paths = json;
      })
      .catch(function(error) { notifyError('Failed to load Backup File List.'); })
      .finally(function() { processing = false; });
	}

	function createBackup() {
	  processing = true;
	  logText = logLines.reset().toText();
    fetch($instance.url + '/deployment/backup-' + this.name, newPostRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        subs.poll(json.url, function(data) {
          logText = logLines.append(data).toText();
          return true;
        })
        .then(function() { notifyInfo('Backup completed. Please check log output for details.'); })
        .finally(reload);
      })
      .catch(function(error) {
        notifyError('Failed to create Backup.');
        processing = false;
      });
	}

	function restoreBackup() {
	  if (!confirm('Are you sure ?')) return;
	  processing = true;
	  logText = logLines.reset().toText();
    let request = newPostRequest();
    request.body = JSON.stringify({ filename: this.name });
    fetch($instance.url + '/deployment/restore-backup', request)
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        subs.poll(json.url, function(data) {
          logText = logLines.append(data).toText();
          return true;
        })
        .then(function() { notifyInfo('Restore from backup completed.'); })
        .finally(function() { processing = false; });
      })
      .catch(function(error) {
        notifyError('Failed to restore Backup.');
        processing = false;
      });
	}

  function deleteBackup() {
    if (!confirm('Are you sure ?')) return;
    processing = true;
    fetch($instance.url + '/backups/' + this.name, newPostRequest())
      .then(function(response) { if (!response.ok) throw new Error('Status: ' + response.status); })
      .catch(function(error) { notifyError('Failed to delete Backup.'); })
      .finally(reload);
  }

  function uploadFile() {
    if (uploadFiles.length === 0) return notifyError('No file specified.');
    let filename = uploadFiles[0].name;
    if (!(filename === filename.replaceAll(' ', '')
        && filename === filename.toLowerCase()
        && (filename.startsWith('runtime-') || filename.startsWith('world-'))
        && filename.endsWith('.zip'))) {
      return notifyError('Filename must start with "runtime-" or "world-", end in ".zip", and be lowercase with no spaces.');
    }
    processing = true;
    let request = rawPostRequest();
    request.body = new FormData();
    request.body.append('file', uploadFiles[0]);
    fetch($instance.url + '/backups/' + filename, request)
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        notifyInfo(filename + ' uploaded successfully.');
      })
      .catch(function(error) { notifyError('Failed to upload ' + filename); })
      .finally(reload);
  }
</script>


<div class="block">
  <table class="table">
    <thead>
      <tr>
        <th>Date</th>
        <th>Size</th>
        <th>Backup</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      {#each paths as path}
        <tr>
          <td>{path.updated}</td>
          <td>{humanFileSize(path.size)}</td>
          <td><a href="{$instance.url + '/backups/' + path.name}">{path.name}</a></td>
          <td class="buttons">
            <button disabled={$serverStatus.running || processing}
                    name="{path.name}" class="button is-warning" on:click={restoreBackup}>Restore</button>
            <button disabled={$serverStatus.running || processing}
                    name="{path.name}" class="button is-danger" on:click={deleteBackup}>Delete</button>
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
  <div class="field">
    <label for="upload-files" class="label">Upload File</label>
    <div class="control pr-6">
      <input id="upload-files" class="input" type="file" bind:files={uploadFiles}>
    </div>
  </div>
  <div class="field">
    <div class="control buttons">
      <button id="upload-file" disabled={processing}
              name="upload" class="button is-warning" on:click={uploadFile}>Upload File</button>
      <button id="backup-runtime" disabled={$serverStatus.running || processing}
              name="runtime" class="button is-success" on:click={createBackup}>Backup Runtime</button>
      <button id="backup-world" disabled={$serverStatus.running || processing}
              name="world" class="button is-primary" on:click={createBackup}>Backup World</button>
    </div>
  </div>
  <div class="field">
    <label for="backups-log" class="label">Backups Log</label>
    <div class="control pr-6">
      <textarea id="backups-log" class="textarea" readonly>{logText}</textarea>
    </div>
  </div>
</div>
