<script>
  import SystemInfo from '$lib/SystemInfo.svelte';
  import ServerLink from '$lib/ServerLink.svelte';
  import Collapsible from '$lib/Collapsible.svelte';
  import CheckStore from '$lib/CheckStore.svelte';
  import InstanceActivity from '$lib/InstanceActivity.svelte';
  import PlayerActivity from '$lib/PlayerActivity.svelte';
  import StoreActions from '$lib/StoreActions.svelte';
  // import SystemLog from '$lib/SystemLog.svelte';
</script>


<SystemInfo />
<ServerLink />
<CheckStore>
  <Collapsible icon="fa-chart-pie" title="Instance Activity">
    <InstanceActivity />
  </Collapsible>
  <Collapsible icon="fa-user-clock" title="Player Activity">
    <PlayerActivity />
  </Collapsible>
  <Collapsible icon="fa-database" title="Store Actions">
    <StoreActions />
  </Collapsible>
</CheckStore>
<!-- SystemLog / -->
