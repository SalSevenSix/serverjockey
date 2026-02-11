<script>
  import { getContext } from 'svelte';
  import { guessTextFile } from '$lib/util/util';
  import { loadAndEditFile } from './hytale.js';
  import FileCollection from '$lib/instance/FileCollection.svelte';

  const instance = getContext('instance');
  const rootpath = '/modfiles';
  const oddjson = /.*\.json[0-9]+$/;

  function canAction(entry) {
    if (entry.type != 'file') return false;
    return guessTextFile(entry.name) || oddjson.test(entry.name);
  }

  function action(path) {
    loadAndEditFile(instance.url(rootpath + path), path);
  }
</script>


<div class="content">
  <p>
    Only .jar or .zip files accepted.
    All mod files present will automatically be loaded when server starts.
  </p>
</div>

<FileCollection path={rootpath} allowDelete={1} filenameHelp="Only .jar and .zip files are accepted."
                validateFilename={function(fn) { return (fn.endsWith('.jar') || fn.endsWith('.zip')); }}
                customMeta={{ name: 'Edit', button: '', icon: 'fa-file-pen', allowAction: 2,
                              canAction: canAction, action: action }} />
