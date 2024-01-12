<script>
  import { getContext } from 'svelte';
  import { notifyInfo, notifyError } from '$lib/util/notifications';
  import { confirmModal } from '$lib/modal/modals';
  import { newPostRequest, rawPostRequest } from '$lib/util/sjgmsapi';
  import FileSystem from '$lib/FileSystem.svelte';
  import SpinnerIcon from '$lib/widget/SpinnerIcon.svelte';

  const instance = getContext('instance');
  const serverStatus = getContext('serverStatus');
  const fnHelp = 'Filename must start with "runtime-" or "world-", end in ".zip", and be lowercase with no spaces.';

  export let hasWorld = true;

  let fileSystem;
  let uploading = false;
  let uploadFiles = [];
  let notifyText = null;

  $: noFileSelected = uploadFiles.length === 0;
  $: cannotUpload = uploading || $serverStatus.state === 'MAINTENANCE';
  $: cannotBackup = $serverStatus.running || cannotUpload;

  $: if (!cannotBackup && notifyText) {
    notifyInfo(notifyText);
    notifyText = null;
  }

  function createBackup() {
    cannotBackup = true;
    fetch(instance.url('/deployment/backup-' + this.name), newPostRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        notifyText = 'Backup completed. Please check log output for details.';
      })
      .catch(function(error) {
        cannotBackup = false;
        notifyError('Failed to create Backup.');
      });
  }

  function restoreBackup(path, callbacks) {
    confirmModal('Restore?\n' + path + '\nExisting files will be overwritten.', function() {
      cannotBackup = callbacks.start();
      let request = newPostRequest();
      request.body = JSON.stringify({ filename: path });
      fetch(instance.url('/deployment/restore-backup'), request)
        .then(function(response) {
          if (!response.ok) throw new Error('Status: ' + response.status);
          callbacks.started('Restored backup. Please check console log output.');
        })
        .catch(function(error) {
          cannotBackup = callbacks.error('Failed to restore ' + path);
        });
    });
  }

  function uploadFile() {
    if (noFileSelected) return;
    let filename = uploadFiles[0].name;
    if (!(filename === filename.replaceAll(' ', '')
        && filename === filename.toLowerCase()
        && (filename.startsWith('runtime-') || filename.startsWith('world-'))
        && filename.endsWith('.zip'))) {
      return notifyError(fnHelp);
    }
    uploading = true;
    let request = rawPostRequest();
    request.body = new FormData();
    request.body.append('file', uploadFiles[0]);
    fetch(instance.url('/backups/' + filename), request)  // Blocks until complete
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        notifyInfo(filename + ' uploaded successfully.');
      })
      .catch(function(error) {
        notifyError('Failed to upload ' + filename);
      })
      .finally(function() {
        uploading = false;
        fileSystem.reload();  // Manual reload bacause upload does not use MAINTENANCE state
      });
  }
</script>


<FileSystem bind:this={fileSystem} rootPath="/backups" allowDelete={2}
            columnsMeta={{ type: false, date: 'Date', name: 'Backup', size: 'Size' }}
            customMeta={{ name: 'Restore', button: 'is-warning', icon: 'fa-undo', action: restoreBackup,
                          sorter: function(a, b) { return b.name.localeCompare(a.name); }}} />

<div class="content">
  <p>
    Please be patient with Backups/Restores/Uploads. These processes may take a while.
    Check the console log to confirm success.
  </p>
  {#if uploading}
    <p class="has-text-weight-bold">
      <SpinnerIcon /> Please keep this section open while uploading...
    </p>
  {/if}
</div>

<div class="block">
  <div class="file is-fullwidth is-info has-name">
    <div class="control buttons mr-2">
      <button name="upload" title="Upload File" class="button is-success"
              disabled={noFileSelected || cannotUpload} on:click={uploadFile}>
        <i class="fa fa-file-arrow-up fa-lg"></i>&nbsp;&nbsp;Upload</button>
    </div>
    <label class="file-label pr-6">
      <input class="file-input" type="file" name="upload-file" bind:files={uploadFiles}>
      <span class="file-cta" title={fnHelp}>
        <span class="file-icon"><i class="fa fa-file-circle-plus"></i></span>
        <span class="file-label">Choose file…</span>
      </span>
      <span class="file-name" title={fnHelp}>
        {noFileSelected ? 'No file selected' : uploadFiles[0].name}
      </span>
    </label>
  </div>
  <div class="block buttons">
    <button name="runtime" title="Backup Runtime" class="button is-primary"
            disabled={cannotBackup} on:click={createBackup}>
      <i class="fa fa-file-archive fa-lg"></i>&nbsp;&nbsp;Backup Runtime</button>
    {#if hasWorld}
      <button name="world" title="Backup World" class="button is-primary"
              disabled={cannotBackup} on:click={createBackup}>
        <i class="fa fa-file-archive fa-lg"></i>&nbsp;&nbsp;Backup World</button>
    {/if}
  </div>
</div>
