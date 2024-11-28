<script>
  import { onMount, onDestroy, getContext } from 'svelte';
  import { humanDuration, chunkArray } from '$lib/util/util';
  import { notifyError } from '$lib/util/notifications';
  import { SubscriptionHelper, newGetRequest } from '$lib/util/sjgmsapi';
  import SpinnerIcon from '$lib/widget/SpinnerIcon.svelte';

  const instance = getContext('instance');
  const subs = new SubscriptionHelper();

  export let hasSteamId = false;

  let loading = true;
  let columnCount = 2 + (hasSteamId ? 1 : 0);
  let players = [];

  $: chunks = chunkArray(players, 15, hasSteamId ? 2 : 3);

  const uptimeClock = setInterval(function() {
    const currentPlayers = players;
    const updatedPlayers = [];
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
    if (data.event === 'CLEAR') {
      players = [];
      return true;
    }
    const loginEvent = (data.event === 'LOGIN');
    if (loginEvent || data.event === 'LOGOUT') {
      const updatedPlayers = players.filter(function(value) {
        return value.name != data.player.name;
      });
      if (loginEvent) {
        updatedPlayers.push(data.player);
      }
      players = updatedPlayers;
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


{#if players.length === 0}
  <div class="block">
    <table class="table">
      <thead><tr>
        {#if hasSteamId}<th>Steam ID</th>{/if}
        <th>Player</th><th>Online</th>
      </tr></thead>
      <tbody id="playersZeroOnline"><tr>
        <td colspan={columnCount}>
          {#if loading}
            <SpinnerIcon /> Loading...
          {:else}
            <i class="fa fa-diamond fa-lg mr-1"></i> Zero players online
          {/if}
        </td>
      </tr></tbody>
    </table>
  </div>
{:else}
  <div class="columns is-gapless mt-1">
    {#each chunks as column, index}
      <div class="column {chunks.length > 2 ? 'is-one-third' : 'is-one-half'}">
        <table class="table">
          {#if index === 0}
            <thead><tr class="table-header">
              {#if hasSteamId}<th id="playersHeaderSteamID">Steam ID</th>{/if}
              <th id="playersHeaderPlayer">Player</th>
              <th id="playersHeaderOnline">Online</th>
            </tr></thead>
          {/if}
          <tbody id="playersColumn{index}">
            {#if index > 0}
              <tr class="table-header"><td colspan={columnCount}></td></tr>
            {/if}
            {#each column as player}
              <tr>
                {#if hasSteamId}
                  <td class="white-space-nowrap">{player.steamid ? player.steamid : 'CONNECTED'}</td>
                {/if}
                <td class="word-break-all player-column notranslate">{player.name}</td>
                <td class="white-space-nowrap online-column notranslate">
                  {player.hasOwnProperty('uptime') ? humanDuration(player.uptime, 2) : ''}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/each}
  </div>
{/if}
<div class="block"></div>


<style>
  .table-header {
    height: 2.1em;
  }

  .player-column {
    min-width: 137px;
  }

  .online-column {
    min-width: 87px;
  }
</style>
