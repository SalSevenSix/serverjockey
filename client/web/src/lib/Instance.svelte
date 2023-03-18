<script>
  import { goto } from '$app/navigation';
  import { onMount, onDestroy } from 'svelte';
  import { get } from 'svelte/store';
  import { sleep } from '$lib/util';
  import { notifyError } from '$lib/notifications';
  import { instance, serverStatus, SubscriptionHelper, newGetRequest } from '$lib/serverjockeyapi';

  serverStatus.set({});
  let subs = new SubscriptionHelper();

  async function setServerStatus(data) {
    let id = Date.now().toString() + Math.random().toString().slice(1);
    data.id = id;
    serverStatus.set(data);
    if (!data.uptime) return;
    let looping = true;
    while (looping) {
      await sleep(20000);
      if (id === get(serverStatus).id) {
        data.uptime += 20000;
        serverStatus.set(data);
      } else {
        looping = false;
      }
    }
  }

  onMount(function() {
    if (!$instance.identity) return goto('/servers');
    fetch($instance.url + '/server', newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        setServerStatus(json);
        subs.start($instance.url + '/server/subscribe', function(data) {
          setServerStatus(data);
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
