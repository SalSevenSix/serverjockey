<script>
  import { humanDuration } from 'common/util/util';

  let { data } = $props();
</script>


<div id="PlayerSummary" class="dashcontainer"><div class="dashpanel statbox is-black">
  <div>
    <h2>Player Summary</h2>
    <table><tbody>
      <tr><th>Unique Players</th><td class="text-align-right">{data.p.results.summary.unique}</td></tr>
      <tr><th>Max Concurrent</th><td class="text-align-right">{data.p.results.summary.online.max}</td></tr>
      <tr><th>Total Sessions</th><td class="text-align-right">{data.p.results.summary.total.sessions}</td></tr>
    </tbody></table>
  </div>
  <div>
    <p class="tpt-value">{humanDuration(data.p.results.summary.total.uptime)}</p>
    <p class="tpt-label">total played time</p>
  </div>
</div></div>


<style>
  .tpt-value {
    font-size: 1.3em;
    font-weight: bold;
  }

  .tpt-label {
    font-size: 0.9em;
  }
</style>
