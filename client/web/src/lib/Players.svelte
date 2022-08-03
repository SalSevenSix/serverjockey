<script>
  import { onMount, onDestroy } from 'svelte';
	import { instance, serverStatus, SubscriptionHelper, newGetRequest } from '$lib/serverjockeyapi';

  let subs = new SubscriptionHelper();
  let players = [];

  let lastRunning = $serverStatus.running;
  $: serverRunningChange($serverStatus.running);
  function serverRunningChange(running) {
    if (lastRunning === $serverStatus.running) return;
    players = [];
    lastRunning = $serverStatus.running;
  }

	onMount(async function() {
	  players = await fetch($instance.url + '/players', newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .catch(function(error) { alert(error); });
    await subs.start($instance.url + '/players/subscribe', function(data) {
      if (data.event === 'login') {
        players = [...players, data.player];
      } else if (data.event === 'logout') {
        players = players.filter(function(value) {
          return value.name != data.player.name;
        });
      }
	    return true;
	  });
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
