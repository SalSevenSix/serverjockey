<script>
  import { chunkArray, humanDuration } from 'common/util/util';
  import { truncName } from '$lib/util';

  let { data } = $props();
</script>


<div id="PlayerOnline" class="dashcontainer"><div class="dashpanel">
  <h2>Players Online&nbsp; ({data.o.length})</h2>
  <div class="flex-columns">
    {#each chunkArray(data.o, 5, 3) as playerColumn}
      <div class="flex-column"><table><tbody>
        {#each playerColumn as playerRow}
          <tr>
            <td class="left">{truncName(playerRow.name, 17)}</td>
            <td class="right">{humanDuration(playerRow.uptime, 'hm')}</td>
          </tr>
        {/each}
      </tbody></table></div>
    {/each}
  </div>
</div></div>
