<script>
  import { onMount, onDestroy, getContext } from 'svelte';
  import { notifyError } from '$lib/notifications';
  import { SubscriptionHelper, newGetRequest } from '$lib/sjgmsapi';
  import Spinner from '$lib/Spinner.svelte';

  const instance = getContext('instance');

  export let hasSteamId = false;

  let subs = new SubscriptionHelper();
  let players = [];
  let loading = true;
  let columnCount = 1 + (hasSteamId ? 1 : 0);

  onMount(function() {
    fetch(instance.url('/players'), newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        players = json;
        subs.start(instance.url('/players/subscribe'), function(data) {
          if (data.event === 'clear') {
            players = [];
            return true;
          }
          if (data.event === 'login' || data.event === 'logout') {
            players = players.filter(function(value) {
              return value.name != data.player.name;
            });
          }
          if (data.event === 'login') {
            players = [...players, data.player];
          }
          return true;
        });
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
        <th>Player</th>
        {#if hasSteamId}<th>Steam ID</th>{/if}
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
          <tr>
            <td>{player.name}</td>
            {#if hasSteamId}
              <td>{(!player.hasOwnProperty('steamid')) ? 'n/a' : player.steamid ? player.steamid : 'LOGGING IN'}</td>
            {/if}
          </tr>
        {/each}
      {/if}
    </tbody>
  </table>
</div>
