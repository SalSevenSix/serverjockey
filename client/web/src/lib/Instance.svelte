<script>
  import { onMount, onDestroy } from 'svelte';
  import { instance, serverStatus, SubscriptionHelper } from '$lib/serverjockeyapi';

  serverStatus.set({});
  let subs = new SubscriptionHelper();

	onMount(async function() {
    let result = await fetch($instance.url + '/server')
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .catch(function(error) { alert('Error: ' + error); });
    serverStatus.set(result);
    await subs.start($instance.url + '/server/subscribe', function(data) {
      serverStatus.set(data);
	    return true;
	  });
	});

	onDestroy(function() {
		subs.stop();
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
