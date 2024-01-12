<script>
  import FileSystem from '$lib/instance/FileSystem.svelte';

  export let rootPath = '/logs';
  export let allowDelete = 0;
  export let confirmDelete = false;
  export let columnsMeta = { type: true, date: false, name: 'Name', size: 'Size' };
  export let sorter = null;
</script>


<FileSystem rootPath={rootPath}
            allowDelete={allowDelete} confirmDelete={confirmDelete}
            columnsMeta={columnsMeta} sorter={sorter} />
