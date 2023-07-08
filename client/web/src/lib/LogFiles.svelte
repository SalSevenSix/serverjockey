<script>
  import FileSystem from '$lib/FileSystem.svelte';

  export let rootPath = '/logs';
  export let allowDelete = false;
  export let columnsMeta = { type: true, date: false, name: 'Name', size: 'Size' };
  export let sorter = null;
</script>

<FileSystem rootPath={rootPath} allowDelete={allowDelete} columnsMeta={columnsMeta} sorter={sorter} />
