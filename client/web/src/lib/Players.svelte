<script>
  import { onMount, onDestroy, getContext } from 'svelte';
  import { humanDuration } from '$lib/util';
  import { notifyError } from '$lib/notifications';
  import { SubscriptionHelper, newGetRequest } from '$lib/sjgmsapi';
  import SpinnerIcon from '$lib/SpinnerIcon.svelte';

  const instance = getContext('instance');

  export let hasSteamId = false;

  let subs = new SubscriptionHelper();
  let players = [];
  let loading = true;
  let columnCount = 2 + (hasSteamId ? 1 : 0);

  let uptimeClock = setInterval(function() {
    let currentPlayers = players;
    let updatedPlayers = [];
    currentPlayers.forEach(function(player) {
      if (player.hasOwnProperty('uptime')) {
        player.uptime += 10000;
      }
      updatedPlayers.push(player);
    });
    if (players === currentPlayers) {
      players = updatedPlayers;
    }
  }, 10000);

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
    clearInterval(uptimeClock);
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
            <SpinnerIcon /> Loading...
          {:else}
            <i class="fa fa-diamond fa-lg mr-1"></i> Zero players online
          {/if}
        </td></tr>
      {:else}
        {#each players as player}
          <tr>
            {#if hasSteamId}
              <td>{player.steamid ? player.steamid : 'CONNECTED'}</td>
            {/if}
            <td>{player.name}</td>
            <td>{player.hasOwnProperty('uptime') ? humanDuration(player.uptime, 2) : ''}</td>
          </tr>
        {/each}
      {/if}
    </tbody>
  </table>
</div>
