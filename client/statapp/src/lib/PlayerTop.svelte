<script>
  import { chunkArray, humanDuration } from 'common/util/util';
  import { compactPlayers } from 'common/activity/player';
  import { truncName } from '$lib/util';

  let { data } = $props();
</script>


<div id="PlayerTop" class="dashcontainer"><div class="dashpanel">
  <h2>Top Players</h2>
  <div class="flex-columns">
    {#each chunkArray(compactPlayers(data.p.results.players, 45), 15, 3) as playerColumn, colindex}
      <div class="flex-column"><table><tbody>
        {#each playerColumn as playerRow, rowindex}
          <tr>
            <td class="idx">{String(colindex * 15 + rowindex + 1).padStart(2, '0')}</td>
            <td class="left">{truncName(playerRow.player, 14)}</td>
            <td class="right">{humanDuration(playerRow.uptime, 'hm', 2)}</td>
          </tr>
        {/each}
      </tbody></table></div>
    {/each}
  </div>
</div></div>
