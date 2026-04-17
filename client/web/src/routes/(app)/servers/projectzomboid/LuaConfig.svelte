<script>
  import { getContext } from 'svelte';
  import { guessTextFile } from '$lib/util/util';
  import { loadAndEditFile } from '$lib/modal/filehelper';
  import FileCollection from '$lib/instance/FileCollection.svelte';

  const instance = getContext('instance');
  const rootpath = '/luafiles';

  function canAction(entry) {
    if (entry.type != 'file') return false;
    return guessTextFile(entry.name);
  }

  function action(path) {
    loadAndEditFile(instance.url(rootpath + path), path);
  }
</script>


<FileCollection path={rootpath} allowDelete={1}
                filenameHelp="Only text files allowed." validateFilename={guessTextFile}
                customMeta={{ name: 'Edit', button: '', icon: 'fa-file-pen',
                              allowAction: 2, canAction: canAction, action: action }} />
