<script>
  import { getContext } from 'svelte';
  import { loadAndEditFile } from './hytale.js';
  import FileSystem from '$lib/instance/FileSystem.svelte';

  const instance = getContext('instance');
  const rootpath = '/universe';

  function action(path) {
    loadAndEditFile(instance.url(rootpath + path), path);
  }
</script>


<FileSystem rootPath={rootpath}
            customMeta={{ name: 'Edit', button: '', icon: 'fa-file-pen', allowAction: 2, action: action }} />
