<script>
  import { onMount, onDestroy, tick } from 'svelte';
  import { notifyInfo, notifyError } from '$lib/notifications';
  import { confirmModal } from '$lib/modals';
  import { sleep, humanFileSize, RollingLog } from '$lib/util';
  import { instance, serverStatus, newGetRequest, newPostRequest,
           rawPostRequest, SubscriptionHelper } from '$lib/serverjockeyapi';

  let subs = new SubscriptionHelper();
  let logLines = new RollingLog();
  let logText = '';
  let logBox;
  let processing = false;
  let paths = [];
  let uploadFiles = [];

	$: if (logText && logBox) {
	  tick().then(function() {
		  logBox.scroll({ top: logBox.scrollHeight });
		});
	}

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
          return b.name.localeCompare(a.name);
        });
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
    let backupName = this.name;
    confirmModal('Restore ' + backupName + ' ?\nExisting files will be overwritten.', function() {
      processing = true;
      logText = logLines.reset().toText();
      let request = newPostRequest();
      request.body = JSON.stringify({ filename: backupName });
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
          .then(function() { notifyInfo('Restored ' + backupName); })
          .finally(function() { processing = false; });
        })
        .catch(function(error) {
          notifyError('Failed to restore ' + backupName);
          processing = false;
        });
    });
  }

  function deleteBackup() {
    let backupName = this.name;
    confirmModal('Delete ' + backupName + ' ?', function() {
      fetch($instance.url + '/backups/' + backupName, newPostRequest())
        .then(function(response) { if (!response.ok) throw new Error('Status: ' + response.status); })
        .catch(function(error) { notifyError('Failed to delete ' + backupName); })
        .finally(reload);
    });
  }

  function uploadFile() {
    if (uploadFiles.length === 0) return notifyError('No file selected.');
    let filename = uploadFiles[0].name;
    if (!(filename === filename.replaceAll(' ', '')
        && filename === filename.toLowerCase()
        && (filename.startsWith('runtime-') || filename.startsWith('world-'))
        && filename.endsWith('.zip'))) {
      return notifyError(
        'Filename must start with "runtime-" or "world-", end in ".zip", and be lowercase with no spaces.');
    }
    processing = true;
    uploadTicker();
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

  async function uploadTicker() {
    let index = 0;
    let rotators = ['--', '\\', '|', '/'];
    while (processing) {
      logText = 'Uploading file  ' + rotators[index];
      index += 1;
      if (index > 3) { index = 0; }
      await sleep(1000);
    }
    logText = '';
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
            <button name="{path.name}" class="button is-warning" title="Restore"
                    disabled={$serverStatus.running || processing} on:click={restoreBackup}>
                    <i class="fa fa-undo"></button>
            <button name="{path.name}" class="button is-danger" title="Delete"
                    disabled={processing} on:click={deleteBackup}>
                    <i class="fa fa-trash"></i></button>
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>

<div class="block">
  <div class="file is-fullwidth is-info has-name">
    <div class="control buttons mr-2">
      <button id="upload-file" disabled={processing}
              name="upload" class="button is-success" on:click={uploadFile}>Upload File</button>
    </div>
    <label class="file-label">
      <input class="file-input" type="file" name="upload-file" bind:files={uploadFiles}>
      <span class="file-cta">
        <span class="file-icon"><i class="fa fa-upload"></i></span>
        <span class="file-label">Choose a file…</span>
      </span>
      <span class="file-name">{uploadFiles.length > 0 ? uploadFiles[0].name : 'No file selected.'}</span>
    </label>
  </div>
  <div class="field">
    <div class="control buttons">
      <button id="backup-runtime" disabled={$serverStatus.running || processing}
              name="runtime" class="button is-primary" on:click={createBackup}>Backup Runtime</button>
      <button id="backup-world" disabled={$serverStatus.running || processing}
              name="world" class="button is-primary" on:click={createBackup}>Backup World</button>
    </div>
  </div>
  <div class="field">
    {#if processing}
      <p>Please be patient, Backup/Restore/Upload process may take a while. Wait for process to complete before
         closing this section or leaving page. Check log output below to confirm success.</p>
    {/if}
    <label for="backups-log" class="label">Backups Log</label>
    <div class="control pr-6">
      <textarea bind:this={logBox} id="backups-log"
                class="textarea is-family-monospace is-size-7" readonly>{logText}</textarea>
    </div>
  </div>
</div>
