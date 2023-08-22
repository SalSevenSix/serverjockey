<script>
  import { onMount, onDestroy, getContext } from 'svelte';
  import { notifyError } from '$lib/notifications';
  import { SubscriptionHelper, newGetRequest } from '$lib/sjgmsapi';
  import PlayerRow from '$lib/PlayerRow.svelte';
  import Spinner from '$lib/Spinner.svelte';

  const instance = getContext('instance');

  export let hasSteamId = false;

  let subs = new SubscriptionHelper();
  let players = [];
  let loading = true;
  let columnCount = 2 + (hasSteamId ? 1 : 0);

  function handlePlayerEvent(data) {
    if (data.event === 'clear') {
      players = [];
      return true;
    }
    let loginEvent = (data.event === 'login');
    if (loginEvent || data.event === 'logout') {
      let result = players.filter(function(value) {
        return value.name != data.player.name;
      });
      if (loginEvent) {
        result.push(data.player);
      }
      players = result;
    }
    return true;
  }

  onMount(function() {
    fetch(instance.url('/players'), newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        players = json;
        subs.start(instance.url('/players/subscribe'), handlePlayerEvent);
      })
      .catch(function(error) {
        notifyError('Failed to load Player list.');
      })
      .finally(function() {
        loading = false;
      });
  });

  onDestroy(function() {
    subs.stop();
  });
</script>


<div class="block">
  <table class="table">
    <thead>
      <tr>
        {#if hasSteamId}<th>Steam ID</th>{/if}
        <th>Player</th>
        <th>Online</th>
      </tr>
    </thead>
    <tbody>
      {#if players.length === 0}
        <tr><td colspan={columnCount}>
          {#if loading}
            <Spinner clazz="fa fa-spinner fa-lg mr-1" /> Loading...
          {:else}
            <i class="fa fa-diamond fa-lg mr-1"></i> Zero players online
          {/if}
        </td></tr>
      {:else}
        {#each players as player}
          <PlayerRow player={player} hasSteamId={hasSteamId} />
        {/each}
      {/if}
    </tbody>
  </table>
</div>
