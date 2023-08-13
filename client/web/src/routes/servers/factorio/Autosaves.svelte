<script>
  import { confirmModal } from '$lib/modals';
  import { newPostRequest } from '$lib/sjgmsapi';
  import { instance } from '$lib/instancestores';
  import FileSystem from '$lib/FileSystem.svelte';

  function restoreAutosave(path, callbacks) {
    confirmModal('Restore?\n' + path + '\nCurrent map will be overwritten.', function() {
      callbacks.start();
      let request = newPostRequest();
      request.body = JSON.stringify({ filename: path });
      fetch($instance.url + '/deployment/restore-autosave', request)
        .then(function(response) {
          if (!response.ok) throw new Error('Status: ' + response.status);
          callbacks.started('Autosave restore complete. Please check console log output.');
        })
        .catch(function(error) {
          callbacks.error('Failed to restore ' + path);
        });
    });
  }
</script>


<FileSystem rootPath="/autosaves" allowDelete={1}
            columnsMeta={{ type: false, date: 'Date', name: 'Autosave', size: 'Size' }}
            customMeta={{ name: 'Restore', button: 'is-warning', icon: 'fa-undo', action: restoreAutosave }} />
