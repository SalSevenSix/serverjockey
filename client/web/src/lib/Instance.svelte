<script>
  import { goto } from '$app/navigation';
  import { onMount, onDestroy } from 'svelte';
  import { notifyError } from '$lib/notifications';
  import { instance, serverStatus, SubscriptionHelper, newGetRequest } from '$lib/serverjockeyapi';

  serverStatus.set({});
  let subs = new SubscriptionHelper();

  onMount(function() {
    if (!$instance.identity) return goto('/servers');
    fetch($instance.url + '/server', newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        serverStatus.set(json);
        subs.start($instance.url + '/server/subscribe', function(data) {
          serverStatus.set(data);
          return true;
        });
      })
      .catch(function(error) { notifyError('Failed to load Server Status.'); });
  });

  onDestroy(function() {
    subs.stop();
  });
</script>


{#if $instance.identity}
  <div class="columns is-centered">
    <div class="column is-half">
      <h1 class="title is-3">{$instance.identity} | {$instance.module}</h1>
    </div>
  </div>
  <slot />
{:else}
  <div class="block">
    <p>No instance set</p>
  </div>
{/if}
