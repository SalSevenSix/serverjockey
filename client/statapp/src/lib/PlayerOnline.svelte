<script>
  import { chunkArray, humanDuration } from 'common/util/util';
  import { truncName } from '$lib/util';

  let { data } = $props();
</script>


<div id="PlayerOnline" class="dashpanel">
  <h2>Players Online&nbsp; ({data.o.length})</h2>
  {#each chunkArray(data.o, 5, 3) as playerColumn}
    <table><tbody>
      {#each playerColumn as playerRow}
        <tr><td>{truncName(playerRow.name, 20)}</td>
        <td>{humanDuration(playerRow.uptime, 'hm')}</td></tr>
      {/each}
    </tbody></table>
  {/each}
</div>
