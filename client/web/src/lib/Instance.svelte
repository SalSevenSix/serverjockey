<script>
  import { onMount, onDestroy } from 'svelte';
  import { instance, serverStatus, SubscriptionHelper, newGetRequest } from '$lib/serverjockeyapi';

  serverStatus.set({});
  let subs = new SubscriptionHelper();

	onMount(async function() {
    let result = await fetch($instance.url + '/server', newGetRequest())
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
