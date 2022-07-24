<script>
  import Instance from '$lib/Instance.svelte';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
  import Players from '$lib/Players.svelte';
</script>


<Instance>
  <div class="columns">
    <div class="column">
      <ServerControls />
      <ServerStatus />
    </div>
    <div class="column">
      <Players />
    </div>
  </div>
</Instance>
