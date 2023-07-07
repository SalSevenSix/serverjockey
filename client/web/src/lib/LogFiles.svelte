<script>
  import FileSystem from '$lib/FileSystem.svelte';

  export let rootPath = '/logs';
  export let allowDelete = false;
  export let columnsMeta = { type: true, date: false, name: 'Name', size: 'Size' };
  export let sortFunction = null;
</script>

{#if sortFunction}
  <FileSystem rootPath={rootPath} allowDelete={allowDelete} columnsMeta={columnsMeta} sortFunction={sortFunction} />
{:else}
  <FileSystem rootPath={rootPath} allowDelete={allowDelete} columnsMeta={columnsMeta} />
{/if}
