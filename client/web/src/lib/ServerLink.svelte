<script>
  import { goto } from '$app/navigation';
  import { onMount, onDestroy } from 'svelte';
  import { baseurl, instance, serverStatus, SubscriptionHelper } from '$lib/serverjockeyapi';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
  import ServerLinkConfig from '$lib/ServerLinkConfig.svelte';

  instance.set({ url: baseurl + '/instances/serverlink' }); // used by ServerControls
  serverStatus.set({}); // used by ServerControls
  let subs = new SubscriptionHelper();

	onMount(async function() {
    const result = await fetch(baseurl + '/instances/serverlink/server')
      .then(function(response) {
         if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .catch(function(error) { alert('Error: ' + error); });
	  if (result.state === 'EXCEPTION') {
		  goto('/setup');
	  } else {
	    serverStatus.set(result);
	  }
    await subs.start(baseurl + '/instances/serverlink/server/subscribe', function(data) {
      serverStatus.set(data);
	    return true;
	  });
	});

	onDestroy(function() {
		subs.stop();
	});
</script>


<div class="columns">
  <div class="column">
    <ServerLinkConfig />
  </div>
  <div class="column">
    <div class="mt-5">
      <ServerControls />
      <ServerStatus />
    </div>
  </div>
</div>
