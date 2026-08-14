<script>
  import { chunkArray, humanDuration } from 'common/util/util';
  import { compactPlayers } from 'common/activity/player';

  let { data } = $props();
</script>


<div id="PlayerTop">
  <h2>Top Players</h2>
  {#each chunkArray(compactPlayers(data.p.results.players, 45), 15, 3) as playerColumn, colindex}
    <table><tbody>
      {#each playerColumn as playerRow, rowindex}
        <tr>
          <td>{colindex * 15 + rowindex + 1}</td>
          <td>{playerRow.player}</td>
          <td>{humanDuration(playerRow.uptime, 'hm')}</td>
        </tr>
      {/each}
    </tbody></table>
  {/each}
</div>
