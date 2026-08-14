<script>
  import { humanDuration } from 'common/util/util';

  let { data } = $props();
</script>


<div id="PlayerSummary">
  <h2>Player Summary</h2>
  <table><tbody>
    <tr><td>Unique Players</td><td>{data.p.results.summary.unique}</td></tr>
    <tr><td>Max Concurrent</td><td>{data.p.results.summary.online.max}</td></tr>
    <tr><td>Total Sessions</td><td>{data.p.results.summary.total.sessions}</td></tr>
    <tr><td>Total Played Time</td><td>{humanDuration(data.p.results.summary.total.uptime)}</td></tr>
  </tbody></table>
</div>
