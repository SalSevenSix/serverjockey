<script>
  import { humanDuration } from 'common/util/util';

  let { data } = $props();
</script>


<div id="PlayerOnline">
  <h2>Players Online ({data.o.length})</h2>
  <table><tbody>
    {#each data.o as player}
      <tr><td>{player.name}</td><td>{humanDuration(player.uptime, 'hm')}</td></tr>
    {/each}
  </tbody></table>
</div>
