<script>
  import Collapsible from '$lib/Collapsible.svelte';
  import ConsoleLog from '$lib/ConsoleLog.svelte';
</script>


<Collapsible icon="fa-scroll" title="ServerJockey Log">
  <ConsoleLog loadUrl={'/system/log/tail'}
              subscribeUrl={'/system/log/subscribe'}
              downloadUrl={'/system/log'} />
</Collapsible>
