<script>
  import ConsoleLog from '$lib/ConsoleLog.svelte';
  import { instance } from '$lib/instancestores';

  export let title = 'Console Log';
  export let canDownload = false;
</script>


<ConsoleLog title={title}
            loadUrl={$instance.url + '/log/tail'}
            subscribeUrl={$instance.url + '/log/subscribe'}
            downloadUrl={canDownload ? $instance.url + '/log' : null} />
