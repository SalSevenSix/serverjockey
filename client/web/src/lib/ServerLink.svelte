<script>
  import { onMount, onDestroy } from 'svelte';
  import { baseurl, instance, serverStatus, subscribeServerStatus } from '$lib/serverjockeyapi';
  import ServerLinkInstructions from '$lib/ServerLinkInstructions.svelte';

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


<ServerLinkInstructions />
