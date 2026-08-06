<script>
  import Collapsible from '$lib/widget/Collapsible.svelte';
  import SystemLog from '$lib/system/SystemLog.svelte';
  import HttpsControls from '$lib/system/HttpsControls.svelte';
  import SteamCmdControls from '$lib/system/SteamCmdControls.svelte';
</script>


<Collapsible icon="fa-gears" title="System">
  <SystemLog />
  <HttpsControls />
  <SteamCmdControls />
</Collapsible>
