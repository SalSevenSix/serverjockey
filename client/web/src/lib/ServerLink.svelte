<script>
  import { baseurl, instance } from '$lib/serverjockeyapi';
  import ServerStatusStore from '$lib/ServerStatusStore.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerLinkConfig from '$lib/ServerLinkConfig.svelte';
  import Collapsible from '$lib/Collapsible.svelte';
  import ConsoleLog from '$lib/ConsoleLog.svelte';

  // used by ServerStatusStore
  instance.set({ url: baseurl + '/instances/serverlink' });
</script>


<ServerStatusStore>
  <div class="columns">
    <div class="column">
      <div class="columns">
        <div class="column">
          <h2 class="title is-5">ServerLink Controls</h2>
          <ServerControls />
          <ServerStatus stateOnly />
        </div>
        <div class="column">
          <h2 class="title is-5">ServerLink Configuration</h2>
          <ServerLinkConfig />
        </div>
      </div>
      <Collapsible title="ServerLink Log">
        <ConsoleLog hasConsoleLogFile />
      </Collapsible>
    </div>
  </div>
</ServerStatusStore>
