<script>
  import { baseurl } from '$lib/sjgmsapi';
  import Collapsible from '$lib/Collapsible.svelte';
  import ConsoleLog from '$lib/ConsoleLog.svelte';
</script>


<Collapsible title="ServerJockey Log">
  <ConsoleLog loadUrl={baseurl + '/system/log/tail'}
              subscribeUrl={baseurl + '/system/log/subscribe'} />
</Collapsible>
