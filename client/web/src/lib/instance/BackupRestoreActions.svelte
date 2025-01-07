<script>
  import { getContext } from 'svelte';
  import { notifyInfo, notifyError } from '$lib/util/notifications';
  import { confirmModal } from '$lib/modal/modals';
  import { newPostRequest } from '$lib/util/sjgmsapi';
  import FileSystem from '$lib/instance/FileSystem.svelte';
  import FileUpload from '$lib/instance/FileUpload.svelte';

  const instance = getContext('instance');
  const serverStatus = getContext('serverStatus');

  let fileSystem;
  let notifyText = null;

  $: cannotBackup = $serverStatus.running || $serverStatus.state === 'MAINTENANCE';

  $: if (!cannotBackup && notifyText) {
    notifyInfo(notifyText);
    notifyText = null;
  }

  const fnHelp = 'Filename must start with "runtime-" or "world-", end in ".zip", and be lowercase with no spaces.';
  function validateFn(filename) {
    return filename === filename.replaceAll(' ', '')
        && filename === filename.toLowerCase()
        && (filename.startsWith('runtime-') || filename.startsWith('world-'))
        && filename.endsWith('.zip');
  }

  function createBackup() {
    cannotBackup = true;
    fetch(instance.url('/deployment/backup-' + this.name), newPostRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        notifyText = 'Backup completed. Please check log output for details.';
      })
      .catch(function() {
        cannotBackup = false;
        notifyError('Failed to create Backup.');
      });
  }

  function restoreBackup(path, callbacks) {
    confirmModal('Restore?\n' + path + '\nExisting files will be overwritten.', function() {
      cannotBackup = callbacks.start();
      const request = newPostRequest();
      request.body = JSON.stringify({ filename: path });
      fetch(instance.url('/deployment/restore-backup'), request)
        .then(function(response) {
          if (!response.ok) throw new Error('Status: ' + response.status);
          callbacks.started('Restored backup. Please check console log output.');
        })
        .catch(function() {
          cannotBackup = callbacks.error('Failed to restore ' + path);
        });
    });
  }
</script>


<FileSystem bind:this={fileSystem} rootPath="/backups" allowDelete={2}
            columnsMeta={{ type: false, date: 'Date', name: 'Backup', size: 'Size' }}
            customMeta={{ name: 'Restore', button: 'is-warning', icon: 'fa-undo', action: restoreBackup }} />

<div class="content">
  <p>
    Backup, Restore and Upload processes may take a while. Check the console log to confirm success.
  </p>
</div>

<div class="mb-2">
  <FileUpload idPrefix="backupRestoreActions" rootPath="/backups"
              filenameHelp={fnHelp} validateFilename={validateFn}
              onCompleted={function() { fileSystem.reload(); }} />
</div>

<div class="block buttons">
  <button id="backupRestoreActionsBackupRuntime" name="runtime" title="Backup Runtime" class="button is-primary"
          disabled={cannotBackup} on:click={createBackup}>
    <i class="fa fa-file-archive fa-lg"></i>&nbsp;&nbsp;Backup Runtime</button>
  <button id="backupRestoreActionsBackupWorld" name="world" title="Backup World" class="button is-primary"
          disabled={cannotBackup} on:click={createBackup}>
    <i class="fa fa-file-archive fa-lg"></i>&nbsp;&nbsp;Backup World</button>
</div>


<style>
  .button {
    min-width: 12em;
  }
</style>
