<script>
  import Collapsible from '$lib/widget/Collapsible.svelte';
  import CheckServerLink from '$lib/svrlink/CheckServerLink.svelte';
  import ServerLinkConfig from '$lib/svrlink/ServerLinkConfig.svelte';
  import ServerStatusStore from '$lib/instance/ServerStatusStore.svelte';
  import ServerControls from '$lib/instance/ServerControls.svelte';
  import ServerConfig from '$lib/instance/ServerConfig.svelte';
  import ServerStatus from '$lib/instance/ServerStatus.svelte';
  import InstanceLog from '$lib/instance/InstanceLog.svelte';
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
