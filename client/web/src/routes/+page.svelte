<script>
  import SystemInfo from '$lib/SystemInfo.svelte';
  import ServerLink from '$lib/ServerLink.svelte';
  import SystemLog from '$lib/SystemLog.svelte';
  import Collapsible from '$lib/Collapsible.svelte';
  import CheckStore from '$lib/CheckStore.svelte';
  import InstanceActivity from '$lib/InstanceActivity.svelte';
</script>


<SystemInfo />
<ServerLink />
<SystemLog />
<CheckStore>
  <Collapsible icon="fa-chart-pie" title="Instance Activity">
    <InstanceActivity />
  </Collapsible>
  <Collapsible icon="fa-user-clock" title="Player Activity">
    <!-- Player Activity -->
  </Collapsible>
</CheckStore>
