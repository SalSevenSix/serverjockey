<script>
  import { getContext } from 'svelte';
  import ConsoleLog from '$lib/widget/ConsoleLog.svelte';

  const instance = getContext('instance');

  export let title = 'Console Log';
  export let canDownload = false;
</script>


<ConsoleLog title={title}
            loadUrl={instance.url('/log/tail')}
            subscribeUrl={instance.url('/log/subscribe')}
            downloadUrl={canDownload ? instance.url('/log') : null} />
