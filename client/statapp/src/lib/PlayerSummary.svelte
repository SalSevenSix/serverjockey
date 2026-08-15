<script>
  import { humanDuration } from 'common/util/util';

  let { data } = $props();
</script>


<div id="PlayerSummary" class="dashpanel" style="height: 7rem;">
  <h2>Player Summary</h2>
  <div style="float: left;">
    <table><tbody>
      <tr><th>Unique Players</th><td>{data.p.results.summary.unique}</td></tr>
      <tr><th>Max Concurrent</th><td>{data.p.results.summary.online.max}</td></tr>
      <tr><th>Total Sessions</th><td>{data.p.results.summary.total.sessions}</td></tr>
    </tbody></table>
  </div><div style="float: right;">
    <strong style="font-size: 1.5rem;">{humanDuration(data.p.results.summary.total.uptime)}</strong>
    <br>
    <span style="font-size: 0.8rem;">total played time</span>
  </div>
</div>
