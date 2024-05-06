<script>
  import Collapsible from '$lib/widget/Collapsible.svelte';
  import SystemLog from '$lib/system/SystemLog.svelte';
  import HttpsControls from '$lib/system/HttpsControls.svelte';
</script>


<Collapsible icon="fa-gears" title="System">
  <SystemLog />
  <HttpsControls />
</Collapsible>
