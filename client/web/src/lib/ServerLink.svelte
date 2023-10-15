<script>
  import ServerStatusStore from '$lib/ServerStatusStore.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
  import ServerConfig from '$lib/ServerConfig.svelte';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerLinkConfig from '$lib/ServerLinkConfig.svelte';
  import Collapsible from '$lib/Collapsible.svelte';
  import InstanceLog from '$lib/InstanceLog.svelte';
</script>


<ServerStatusStore identity="serverlink">
  <div class="columns">
    <div class="column">
      <div class="columns">
        <div class="column">
          <h2 class="title is-5">ServerLink Controls</h2>
          <ServerControls />
          <ServerConfig />
          <ServerStatus stateOnly />
        </div>
        <div class="column">
          <h2 class="title is-5">ServerLink Configuration</h2>
          <ServerLinkConfig />
        </div>
      </div>
      <Collapsible title="ServerLink Log">
        <InstanceLog title={''} canDownload />
      </Collapsible>
    </div>
  </div>
</ServerStatusStore>
