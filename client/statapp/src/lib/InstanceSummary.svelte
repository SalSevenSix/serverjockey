<script>
  import { floatToPercent, humanDuration } from 'common/util/util';

  let { data } = $props();
</script>


<div id="InstanceTitle">
  <h1>Instance: {data.s.instance}</h1>
</div>

<div id="InstanceSummary">
  <table><tbody>
    <tr><td>Status</td><td>{data.s.state}</td></tr>
    <tr><td>Version</td><td>{data.s.details.version}</td></tr>
    <tr><td>Connect</td><td>{data.s.details.ip}:{data.s.details.port}</td></tr>
    <tr><td>Date</td><td>1996-07-05 10:40</td></tr>
    <tr><td></td><td></td></tr>
    <tr><td></td><td></td></tr>
  </tbody></table>
</div>

<div id="ReportSummary">
  <ul>
    <li>Activity from last {humanDuration(data.i.results.range)} </li>
    <li>Server uptime {humanDuration(data.i.results.uptime)} ({floatToPercent(data.i.results.available)}) </li>
  </ul>
</div>
