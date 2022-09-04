<script>
  import { onMount, onDestroy } from 'svelte';
  import { notifyError } from '$lib/notifications';
	import { instance, serverStatus, SubscriptionHelper, newGetRequest } from '$lib/serverjockeyapi';

  let subs = new SubscriptionHelper();
  let players = [];

  let lastRunning = $serverStatus.running;
  $: serverRunningChange($serverStatus.running);
  function serverRunningChange(running) {
    if (lastRunning === true && running === false) {
      players = [];
    }
    lastRunning = running;
  }

	onMount(function() {
	  fetch($instance.url + '/players', newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        players = json;
        subs.start($instance.url + '/players/subscribe', function(data) {
          if (data.event === 'login') {
            players = [...players, data.player];
          } else if (data.event === 'logout') {
            players = players.filter(function(value) {
              return value.name != data.player.name;
            });
          }
          return true;
        });
      })
      .catch(function(error) { notifyError('Failed to load Player List.'); });
	});

	onDestroy(function() {
		subs.stop();
	});
</script>


<div class="block">
  <h2 class="title is-5">{players.length} Players Online</h2>
  <table class="table">
    <thead>
      <tr>
        <th>Name</th>
        <th>Steam ID</th>
      </tr>
    </thead>
    <tbody>
      {#each players as player}
        <tr>
          <td>{player.name}</td>
          <td>{(player.steamid == false) ? 'n/a' : player.steamid ? player.steamid : 'LOGGING IN'}</td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>
