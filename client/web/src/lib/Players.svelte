<script>
  import { onMount, onDestroy } from 'svelte';
	import { instance, subscribeAndPoll } from '$lib/serverjockeyapi';

  let polling = true;
  let players = [];
	onMount(async function() {
	  players = await fetch($instance.url + '/players')
      .then(function(response) { return response.json(); })
      .catch(function(error) { alert(error); });
    subscribeAndPoll($instance.url + '/players/subscribe', function(data) {
	    if (data == null || !polling) return polling;
	      if (data.event === 'login') {
	        players = [...players, data.player];
	      } else if (data.event === 'logout') {
	        players = players.filter(function(value) {
	          return value.name != data.player.name;
	        });
	      }
	    return polling;
	  });
	});

	onDestroy(function() {
		polling = false;
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
