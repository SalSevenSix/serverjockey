<script>
  import ServerStatusStore from '$lib/ServerStatusStore.svelte';
  import Instance from '$lib/Instance.svelte';
  import Collapsible from '$lib/Collapsible.svelte';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerConfig from '$lib/ServerConfig.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
  import InstanceLog from '$lib/InstanceLog.svelte';
</script>


<ServerStatusStore><Instance>
  <div class="columns">
    <div class="column">
      <ServerControls />
      <ServerConfig />
      <ServerStatus />
    </div>
  </div>
  <div class="columns">
    <div class="column">
      <InstanceLog />
    </div>
  </div>
</Instance></ServerStatusStore>
