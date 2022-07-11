<script>
  import { onMount, onDestroy } from 'svelte';
  import { baseurl, instance, serverStatus, subscribeServerStatus } from '$lib/serverjockeyapi';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
  import ServerLinkConfig from '$lib/ServerLinkConfig.svelte';

  instance.set({ url: baseurl + '/instances/serverlink' });
  let polling = true;

	onMount(async function() {
	  serverStatus.set(await subscribeServerStatus($instance, function(data) {
	    if (data == null || !polling) return polling;
	    serverStatus.set(data);
	    return polling;
	  }));
	});

	onDestroy(function() {
		polling = false;
	});
</script>


<div class="block">
  <h2 class="subtitle">ServerLink</h2>
</div>
<ServerLinkConfig />
<ServerStatus />
<ServerControls />
