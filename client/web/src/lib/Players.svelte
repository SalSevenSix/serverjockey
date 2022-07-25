<script>
  import { onMount, onDestroy } from 'svelte';
	import { instance, SubscriptionHelper } from '$lib/serverjockeyapi';

  let subs = new SubscriptionHelper();
  let players = [];

	onMount(async function() {
	  players = await fetch($instance.url + '/players')
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


<div class="column">
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
  <p>{players.length} players currently online</p>
</div>
