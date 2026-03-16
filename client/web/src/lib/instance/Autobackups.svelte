<script>
  import { getContext } from 'svelte';
  import { notifyInfo, notifyError } from '$lib/util/notifications';
  import { confirmModal } from '$lib/modal/modals';
  import { newPostRequest } from '$lib/util/sjgmsapi';
  import FileSystem from '$lib/instance/FileSystem.svelte';

  const instance = getContext('instance');

  export let noMaint = false;
  export let allowDelete = 1;
  export let columnsMeta = { date: 'Date', name: 'Backup', size: 'Size' };

  function restoreAutobackup(path, callbacks) {
    if (noMaint) { callbacks = null; }
    confirmModal('Restore?\n' + path + '\nCurrent save will be overwritten.', function() {
      if (callbacks) { callbacks.start(); }
      const request = newPostRequest();
      request.body = JSON.stringify({ filename: path });
      fetch(instance.url('/deployment/restore-autobackup'), request)
        .then(function(response) {
          if (!response.ok) throw new Error('Status: ' + response.status);
          const infoMessage = 'Autobackup restore complete. Please check console log output.';
          if (callbacks) { callbacks.started(infoMessage); }
          else { notifyInfo(infoMessage); }
        })
        .catch(function() {
          const errorMessage = 'Failed to restore ' + path;
          if (callbacks) { callbacks.error(errorMessage); }
          else { notifyError(errorMessage); }
        });
    });
  }
</script>


<FileSystem rootPath="/autobackups" allowDelete={allowDelete} columnsMeta={columnsMeta}
  customMeta={{ name: 'Restore', button: 'is-warning', icon: 'fa-arrow-rotate-left', action: restoreAutobackup }} />
