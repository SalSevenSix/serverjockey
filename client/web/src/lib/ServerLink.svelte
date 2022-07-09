<script>
  import { onMount, onDestroy } from 'svelte';
  import { instance, serverStatus, subscribeServerStatus } from '$lib/serverjockeyapi';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
  import ServerLinkConfig from '$lib/ServerLinkConfig.svelte';

  instance.set({ url: 'http://localhost:6164/instances/serverlink' });
  let polling = true;

	onMount(async function() {
	  serverStatus.set(await subscribeServerStatus($instance, function(data) {
	    if (data == null) return polling;
	    serverStatus.set(data);
	    return polling;
	  }));
	});

	onDestroy(function() {
		polling = false;
	});
</script>


<div>
  <ServerLinkConfig />
  <ServerStatus />
  <ServerControls />
</div>
