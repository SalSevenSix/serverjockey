<script>
  import Instance from '$lib/Instance.svelte';
  import Collapsible from '$lib/Collapsible.svelte';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
  import ConsoleLog from '$lib/ConsoleLog.svelte';
</script>


<Instance>
  <div class="columns">
    <div class="column">
      <ServerControls />
      <ServerStatus />
    </div>
  </div>
  <div class="columns">
    <div class="column">
      <ConsoleLog />
    </div>
  </div>
</Instance>
