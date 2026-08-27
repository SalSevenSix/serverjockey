<script>
  import { floatToPercent, humanDuration } from 'common/util/util';

  let { data } = $props();

  function statusClass(available) {
    if (available < 0.5) return 'is-red';
    if (available > 0.9) return 'is-green';
    return 'is-yellow';
  }
</script>


<div id="InstanceSummary" class="dashcontainer"><div class="dashpanel statbox {statusClass(data.i.results.available)}">
  <div>
    <h2>Availability</h2>
    <table><tbody>
      <tr><th>Last</th><td class="text-align-right">{humanDuration(data.i.results.range)}</td></tr>
      <tr><th>Uptime</th><td class="text-align-right">{humanDuration(data.i.results.uptime)}</td></tr>
    </tbody></table>
  </div>
  <div><p class="availability-percent">{floatToPercent(data.i.results.available)}</p></div>
</div></div>
