<script>
  import { fTrue } from '$lib/util/util';
  import FileSystem from '$lib/instance/FileSystem.svelte';
  import FileUpload from '$lib/instance/FileUpload.svelte';

  export let path;
  export let idPrefix = "fileCollection";
  export let filenameHelp = 'Please choose a valid filename.';
  export let validateFilename = fTrue;

  let fileSystem;
</script>


<FileSystem bind:this={fileSystem} rootPath={path} allowDelete={2} />
<FileUpload idPrefix={idPrefix} rootPath={path} multiple
            filenameHelp={filenameHelp} validateFilename={validateFilename}
            onCompleted={function() { fileSystem.reload(); }} />
