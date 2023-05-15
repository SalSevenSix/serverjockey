<script>
  import { onMount } from 'svelte';
  import { notifyInfo, notifyError } from '$lib/notifications';
  import { confirmModal } from '$lib/modals';
  import { sleep, humanFileSize } from '$lib/util';
  import { instance, serverStatus, newGetRequest, newPostRequest, rawPostRequest } from '$lib/serverjockeyapi';

  let uploading = false;
  let rotatorText = '';
  let reloadRequired = false;
  let notifyText = null;
  let paths = [];
  let uploadFiles = [];

  $: cannotMaintenance = $serverStatus.state === 'MAINTENANCE';
  $: cannotProcess = $serverStatus.running || cannotMaintenance;
  $: if (!cannotProcess && reloadRequired) {
    reloadRequired = false;
    reload();
  }
  $: if (!cannotProcess && notifyText) {
    notifyInfo(notifyText);
    notifyText = null;
  }

  onMount(reload);

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
      .catch(function(error) {
        notifyError('Failed to load Backup File List.');
      });
  }

  function createBackup() {
    cannotProcess = true;
    fetch($instance.url + '/deployment/backup-' + this.name, newPostRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        reloadRequired = true;
        notifyText = 'Backup completed. Please check log output for details.';
      })
      .catch(function(error) {
        notifyError('Failed to create Backup.');
        cannotProcess = false;
      });
  }

  function restoreBackup() {
    let backupName = this.name;
    confirmModal('Restore ' + backupName + ' ?\nExisting files will be overwritten.', function() {
      cannotProcess = true;
      let request = newPostRequest();
      request.body = JSON.stringify({ filename: backupName });
      fetch($instance.url + '/deployment/restore-backup', request)
        .then(function(response) {
          if (!response.ok) throw new Error('Status: ' + response.status);
          notifyText = 'Restored ' + backupName;
        })
        .catch(function(error) {
          notifyError('Failed to restore ' + backupName);
          cannotProcess = false;
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
    uploading = true;
    uploadTicker();
    let request = rawPostRequest();
    request.body = new FormData();
    request.body.append('file', uploadFiles[0]);
    fetch($instance.url + '/backups/' + filename, request)
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        notifyInfo(filename + ' uploaded successfully.');
      })
      .catch(function(error) {
        notifyError('Failed to upload ' + filename);
      })
      .finally(function() {
        uploading = false;
        reload();
      });
  }

  async function uploadTicker() {
    let index = 0;
    let rotators = ['--', '\\', '|', '/'];
    while (uploading) {
      rotatorText = rotators[index];
      index += 1;
      if (index > 3) { index = 0; }
      await sleep(1000);
    }
    rotatorText = '';
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
                    disabled={cannotProcess} on:click={restoreBackup}>
                    <i class="fa fa-undo"></button>
            <button name="{path.name}" class="button is-danger" title="Delete"
                    disabled={cannotMaintenance} on:click={deleteBackup}>
                    <i class="fa fa-trash"></i></button>
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>

<div class="content">
  <p>
    Please be patient with Backups/Restores/Uploads. These processes may take a while.
    Check the console log to confirm success.
  </p>
  {#if uploading}
    <p class="has-text-weight-bold">
      Uploads require this section to remain open until complete... {rotatorText}
    </p>
  {/if}
</div>

<div class="block">
  <div class="file is-fullwidth is-info has-name">
    <div class="control buttons mr-2">
      <button name="upload" class="button is-success"
              disabled={cannotMaintenance} on:click={uploadFile}>Upload File</button>
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
      <button name="runtime" class="button is-primary"
              disabled={cannotProcess} on:click={createBackup}>Backup Runtime</button>
      <button name="world" class="button is-primary"
              disabled={cannotProcess} on:click={createBackup}>Backup World</button>
    </div>
  </div>
</div>
