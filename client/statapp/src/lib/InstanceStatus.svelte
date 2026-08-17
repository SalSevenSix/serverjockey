<script>
  let { data } = $props();
</script>


<div id="InstanceStatus" class="dashcontainer"><div class="dashpanel statbox is-{data.s.running ? 'green' : 'red'}">
  <div>
    <h2>Server Status</h2>
    <table><tbody>
      <tr><th>State</th><td>{data.s.state}</td></tr>
      <tr><th>Version</th><td>{data.s.details.version}</td></tr>
      <tr><th>Connect</th><td>{data.s.details.ip}:{data.s.details.port}</td></tr>
      {#if data.s.details.ingametime}
        <tr><th>Game Time</th><td>{data.s.details.ingametime}</td></tr>
      {/if}
    </tbody></table>
  </div>
  <div><p class="running-value">{data.s.running ? 'UP' : 'DOWN'}</p></div>
</div></div>


<style>
  .running-value {
    font-size: 1.3em;
    font-weight: bold;
  }
</style>
