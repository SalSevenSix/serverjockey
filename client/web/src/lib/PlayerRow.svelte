<script>
  import { onDestroy } from 'svelte';
  import { humanDuration } from '$lib/util';

  export let player;
  export let hasSteamId = false;

  let uptimeClock = setInterval(function() {
    if (player.hasOwnProperty('uptime')) {
      player.uptime += 10000;
    }
  }, 10000);

  onDestroy(function() {
    clearInterval(uptimeClock);
  });
</script>


<tr>
  {#if hasSteamId}
    <td>{(!player.hasOwnProperty('steamid')) ? 'n/a' : player.steamid ? player.steamid : 'LOGGING IN'}</td>
  {/if}
  <td>{player.name}</td>
  <td>{player.uptime ? humanDuration(player.uptime, 2) : ''}</td>
</tr>
