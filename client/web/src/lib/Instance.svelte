<script>
  import { onMount, onDestroy } from 'svelte';
  import { instance, serverStatus, subscribeServerStatus } from '$lib/serverjockeyapi';

  serverStatus.set({});

  let polling = true;
	onMount(async function() {
	  let status = await subscribeServerStatus($instance, function(data) {
	    if (data == null || !polling) return polling;
	    serverStatus.set(data);
	    return polling;
	  });
	  serverStatus.set(status);
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
  <slot />
{:else}
  <div class="block">
    <p>No instance set</p>
  </div>
{/if}

<div class="content">
  <p><a href="/servers">BACK</a> to Servers</p>
</div>
