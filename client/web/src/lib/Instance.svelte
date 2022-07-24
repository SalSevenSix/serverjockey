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


{#if $instance.identity}
  <div class="columns is-centered">
    <div class="column is-half">
      <h1 class="title is-3">{$instance.identity} ({$instance.module})</h1>
    </div>
  </div>
  <div class="columns">
    <div class="column">
      <ServerControls />
      <ServerStatus />
    </div>
    <slot />
  </div>
{:else}
  <div class="block">
    <p>No instance set</p>
  </div>
{/if}

<div class="content">
  <p><a href="/servers">BACK</a> to Servers</p>
</div>
