<script>
  import Instance from '$lib/Instance.svelte';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
</script>


<Instance>
  <div class="columns">
    <div class="column">
      <ServerControls />
      <ServerStatus />
    </div>
  </div>
</Instance>
