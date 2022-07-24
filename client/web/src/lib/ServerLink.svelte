<script>
  import { onMount, onDestroy } from 'svelte';
  import { goto } from '$app/navigation';
  import { baseurl, instance, serverStatus, subscribeServerStatus } from '$lib/serverjockeyapi';
  import ServerControls from '$lib/ServerControls.svelte';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerLinkConfig from '$lib/ServerLinkConfig.svelte';

  instance.set({ url: baseurl + '/instances/serverlink' });
  serverStatus.set({});

  let polling = true;
	onMount(async function() {
	  let initialStatus = await subscribeServerStatus($instance, function(data) {
	    if (data == null || !polling) return polling;
	    serverStatus.set(data);
	    return polling;
	  });
	  if (initialStatus.state === 'EXCEPTION') {
		  goto('/setup');
	  } else {
	    serverStatus.set(initialStatus);
	  }
	});

	onDestroy(function() {
		polling = false;
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
