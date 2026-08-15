<script>
  let { data } = $props();
</script>


<div id="InstanceStatus" class="dashpanel container">
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
  <div>{data.s.running ? 'UP' : 'DOWN'}</div>
</div>


<style>
  .container {
    display: flex;
    align-items: center;
    background: linear-gradient(
      to right,
      rgba(0, 0, 0, 0.7) 0%,
      rgba(0, 16, 0, 0.6) 66%,
      lime 90%
    );
  }

  .container > div:first-child {
    flex: 0 0 auto;
  }

  .container > div:last-child {
    flex: 1;
    text-align: right;
    padding-right: 8vw;
    color: black;
  }
</style>
