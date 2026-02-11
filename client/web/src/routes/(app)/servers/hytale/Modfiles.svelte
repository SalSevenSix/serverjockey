<script>
  import { getContext } from 'svelte';
  import { guessTextFile } from '$lib/util/util';
  import { notifyInfo, notifyError } from '$lib/util/notifications';
  import { textAreaModal } from '$lib/modal/modals';
  import { newPostRequest, newGetRequest } from '$lib/util/sjgmsapi';
  import FileCollection from '$lib/instance/FileCollection.svelte';

  const instance = getContext('instance');
  const modfiles = '/modfiles';
  const oddjson = /.*\.json[0-9]+$/;

  function canAction(entry) {
    if (entry.type != 'file') return false;
    return guessTextFile(entry.name) || oddjson.test(entry.name);
  }

  function save(path, text) {
    const request = newPostRequest('text/plain');
    request.body = text;
    fetch(instance.url(modfiles + path), request)
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        notifyInfo(path + ' saved.');
      })
      .catch(function() {
        notifyError('Failed to update ' + path);
      });
  }

  function load(path) {
    fetch(instance.url(modfiles + path), newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.text();
      })
      .then(function(text) {
        textAreaModal(path, text, function(updated) { save(path, updated); });
      })
      .catch(function() {
        notifyError('Failed to load ' + path);
      });
  }
</script>


<div class="content">
  <p>
    Only .jar or .zip files accepted.
    All mod files present will automatically be loaded when server starts.
  </p>
</div>

<FileCollection path={modfiles} allowDelete={1} filenameHelp="Only .jar and .zip files are accepted."
                validateFilename={function(fn) { return (fn.endsWith('.jar') || fn.endsWith('.zip')); }}
                customMeta={{ name: 'Edit', button: '', icon: 'fa-file-pen', allowAction: 2,
                              canAction: canAction, action: load }} />
