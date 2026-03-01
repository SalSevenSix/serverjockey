<script>
  import { getContext } from 'svelte';
  import { guessTextFile } from '$lib/util/util';
  import { loadAndEditFile } from './hytale.js';
  import FileSystem from '$lib/instance/FileSystem.svelte';

  const instance = getContext('instance');
  const rootpath = '/mod/configs';
  const oddjson = /.*\.json[0-9]+$/;

  function canAction(entry) {
    if (entry.type != 'file') return false;
    return guessTextFile(entry.name) || oddjson.test(entry.name);
  }

  function action(path) {
    loadAndEditFile(instance.url(rootpath + path), path);
  }
</script>


<FileSystem rootPath={rootpath} allowDelete={1}
            customMeta={{ name: 'Edit', button: '', icon: 'fa-file-pen',
                          allowAction: 2, canAction: canAction, action: action }} />
