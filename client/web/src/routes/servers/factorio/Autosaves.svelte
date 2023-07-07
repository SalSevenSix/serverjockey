<script>
  import { notifyError } from '$lib/notifications';
  import { confirmModal } from '$lib/modals';
  import { instance, newPostRequest } from '$lib/sjgmsapi';
  import FileSystem from '$lib/FileSystem.svelte';

  function restoreAutosave(url, startCallback, startedCallback) {
    let filename = url.split('/');
    filename = filename[filename.length - 1];
    confirmModal('Restore ' + filename + ' ?\nCurrent map will be overwritten.', function() {
      startCallback();
      let request = newPostRequest();
      request.body = JSON.stringify({ filename: filename });
      fetch($instance.url + '/deployment/restore-autosave', request)
        .then(function(response) {
          if (!response.ok) throw new Error('Status: ' + response.status);
          startedCallback('Autosave restore complete. Please check console log output.');
        })
        .catch(function(error) { notifyError('Failed to restore ' + filename); });
    });
  }
</script>


<FileSystem rootPath="/autosaves" allowDelete
            columnsMeta={{ type: false, date: 'Date', name: 'Autosave', size: 'Size' }}
            customMeta={{ name: 'Restore', button: 'is-warning', icon: 'fa-undo', action: restoreAutosave }} />
