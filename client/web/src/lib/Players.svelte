<script>
  import { onMount, onDestroy } from 'svelte';
  import { notifyError } from '$lib/notifications';
  import { instance, SubscriptionHelper, newGetRequest } from '$lib/sjgmsapi';
  import Spinner from '$lib/Spinner.svelte';
  // TODO probably should HTML escape names

  let subs = new SubscriptionHelper();
  let players = [];
  let loading = true;

  onMount(function() {
    fetch($instance.url + '/players', newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        players = json;
        subs.start($instance.url + '/players/subscribe', function(data) {
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
        <th>Steam ID</th>
      </tr>
    </thead>
    <tbody>
      {#if players.length === 0}
        <tr><td colspan="2">
          {#if loading}
            <Spinner clazz="fa fa-arrows-spin fa-lg mr-1" /> Loading...
          {:else}
            <i class="fa fa-triangle-exclamation fa-lg mr-1"></i> Zero players online
          {/if}
        </td></tr>
      {:else}
        {#each players as player}
          <tr>
            <td>{player.name}</td>
            <td>{(!player.hasOwnProperty('steamid')) ? 'n/a' : player.steamid ? player.steamid : 'LOGGING IN'}</td>
          </tr>
        {/each}
      {/if}
    </tbody>
  </table>
</div>
