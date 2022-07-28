<script>
  import { onMount, onDestroy } from 'svelte';
  import { humanFileSize, ReverseRollingLog } from '$lib/util';
  import { instance, serverStatus, newGetRequest, newPostRequest, SubscriptionHelper } from '$lib/serverjockeyapi';

  let subs = new SubscriptionHelper();
  let logLines = new ReverseRollingLog();
  let logText = '';
  let processing = false;
  let paths = [];

	onMount(reload);

	onDestroy(function() {
		subs.stop();
	});

  function processingDone() {
    processing = false;
    reload();
  }

	async function reload() {
	  let result = await fetch($instance.url + '/backups', newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .catch(function(error) { alert('Error ' + error); });
    result.sort(function(a, b) {
      return a.name.localeCompare(b.name);
    });
    result.reverse();
    paths = result;
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
        .finally(processingDone);
      })
      .catch(function(error) {
        alert('Error ' + error);
        processingDone();
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
        .finally(processingDone);
      })
      .catch(function(error) {
        alert('Error ' + error);
        processingDone();
      });
	}

  function deleteBackup() {
    if (!confirm('Are you sure ?')) return;
    processing = true;
    fetch($instance.url + '/backups/' + this.name, newPostRequest())
      .then(function(response) { if (!response.ok) throw new Error('Status: ' + response.status); })
      .catch(function(error) { alert('Error ' + error); })
      .finally(processingDone);
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
            <button disabled={$serverStatus.running || processing} name="{path.name}" class="button is-warning" on:click={restoreBackup}>Restore</button>
            <button disabled={$serverStatus.running || processing} name="{path.name}" class="button is-danger" on:click={deleteBackup}>Delete</button>
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
  <div class="field">
    <div class="control buttons">
      <button id="backup-runtime" disabled={$serverStatus.running || processing} name="runtime" class="button is-success" on:click={createBackup}>Backup Runtime</button>
      <button id="backup-world" disabled={$serverStatus.running || processing} name="world" class="button is-primary" on:click={createBackup}>Backup World</button>
    </div>
  </div>
  <div class="field">
    <label for="backups-log" class="label">Backups Log</label>
    <div class="control pr-6">
      <textarea id="backups-log" class="textarea" readonly>{logText}</textarea>
    </div>
  </div>
</div>
