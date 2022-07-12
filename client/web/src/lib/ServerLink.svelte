<script>
  import { onMount, onDestroy } from 'svelte';
  import { baseurl, instance, serverStatus, subscribeServerStatus } from '$lib/serverjockeyapi';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
  import ServerLinkConfig from '$lib/ServerLinkConfig.svelte';
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
<hr />

<div class="block">
  <h3 class="title is-4">ServerLink Configuration</h3>
</div>
<ServerLinkConfig />

<div class="block">
  <h3 class="title is-4">ServerLink Console</h3>
</div>
<ServerStatus />
<ServerControls />

<div class="block">
  <hr />
  <p>Take me to <a href="/servers">Servers</a></p>
</div>
