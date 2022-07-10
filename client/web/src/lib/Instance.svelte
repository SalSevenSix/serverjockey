<script>
  import { onMount, onDestroy } from 'svelte';
  import { instance, serverStatus, subscribeServerStatus } from '$lib/serverjockeyapi';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerControls from '$lib/ServerControls.svelte';

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


{#if $instance.name}
  <h1>{$instance.name} ({$instance.module})</h1>
  <ServerStatus />
  <ServerControls />

  <slot />

{:else}
  <p>No instance set</p>
{/if}
<p><a href="/instances">BACK</a> to Instances</p>
