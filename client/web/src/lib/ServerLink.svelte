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


<CheckServerLink let:hasToken={hasToken}>
  <Collapsible icon="fa-robot" title="ServerLink" open={!hasToken}>
    <ServerStatusStore identity="serverlink">
      <div class="columns">
        <div class="column">
          <div class="columns">
            <div class="column">
              <h2 class="title is-5">Controls</h2>
              <ServerControls />
              <ServerConfig />
              <ServerStatus stateOnly />
            </div>
            <div class="column">
              <h2 class="title is-5">Configuration</h2>
              <div class="block mr-6"><ServerLinkConfig /></div>
            </div>
          </div>
          <InstanceLog canDownload />
        </div>
      </div>
    </ServerStatusStore>
  </Collapsible>
</CheckServerLink>
