<script>
  import ServerStatus from '$lib/ServerStatus.svelte';

  let instance = { url: 'http://localhost:6164/instances/serverlink' }
</script>


<ServerStatus instance={instance} />
