<script>
  import { getContext } from 'svelte';
  import { guessTextFile } from '$lib/util/util';
  import { loadAndEditFile } from '$lib/modal/filehelper';
  import FileSystem from '$lib/instance/FileSystem.svelte';
  import ConfigFile from '$lib/instance/ConfigFile.svelte';

  const instance = getContext('instance');
  const rootpath = '/plugin/configs';

  function canAction(entry) {
    if (entry.type != 'file') return false;
    return guessTextFile(entry.name);
  }

  function action(path) {
    loadAndEditFile(instance.url(rootpath + path), path);
  }
</script>


<FileSystem rootPath={rootpath} allowDelete={1}
            customMeta={{ name: 'Edit', button: '', icon: 'fa-file-pen',
                          allowAction: 2, canAction: canAction, action: action }} />
<ConfigFile name="Doorstop Config" path="/config/doorstopconf" />
