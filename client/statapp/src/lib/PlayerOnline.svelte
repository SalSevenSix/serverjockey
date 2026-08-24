<script>
  import { chunkArray, humanDuration } from 'common/util/util';
  import { truncName } from '$lib/util';

  let { data } = $props();
</script>


<div id="PlayerOnline" class="dashcontainer"><div class="dashpanel minheight">
  <h2>Players Online&nbsp; ({data.o.length})</h2>
  <div class="flex-columns">
    {#each chunkArray(data.o, 5, 3) as playerColumn}
      <div class="flex-column"><table><tbody>
        {#each playerColumn as playerRow}
          <tr>
            <td class="left">{truncName(playerRow.name, 16)}</td>
            <td class="right">{humanDuration(playerRow.uptime, 'hm', 2)}</td>
          </tr>
        {/each}
      </tbody></table></div>
    {/each}
  </div>
</div></div>


<style>
  .minheight {
    min-height: 3em;
  }
</style>
