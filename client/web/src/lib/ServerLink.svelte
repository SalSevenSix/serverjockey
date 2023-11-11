<script>
  import CheckServerLink from '$lib/CheckServerLink.svelte';
  import ServerStatusStore from '$lib/ServerStatusStore.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
  import ServerConfig from '$lib/ServerConfig.svelte';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerLinkConfig from '$lib/ServerLinkConfig.svelte';
  import Collapsible from '$lib/Collapsible.svelte';
  import InstanceLog from '$lib/InstanceLog.svelte';
</script>


<CheckServerLink><ServerStatusStore identity="serverlink">
  <Collapsible icon="fa-gears" title="ServerLink" open>
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
      </div>
    </div>
  </Collapsible>
  <Collapsible icon="fa-scroll" title="ServerLink Log">
    <InstanceLog title={''} canDownload />
  </Collapsible>
</ServerStatusStore></CheckServerLink>
