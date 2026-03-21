<script>
  import { fTrue } from 'common/util/util';
  import FileSystem from '$lib/instance/FileSystem.svelte';
  import FileUpload from '$lib/instance/FileUpload.svelte';

  export let path;
  export let idPrefix = 'fileCollection';
  export let filenameHelp = 'Please choose a valid filename.';
  export let validateFilename = fTrue;
  export let allowDelete = 2;
  export let customMeta = null;

  let fileSystem;
</script>


<FileSystem bind:this={fileSystem} rootPath={path} allowDelete={allowDelete} customMeta={customMeta} />
<FileUpload idPrefix={idPrefix} rootPath={path} multiple
            filenameHelp={filenameHelp} validateFilename={validateFilename}
            onCompleted={function() { fileSystem.reload(); }} />
