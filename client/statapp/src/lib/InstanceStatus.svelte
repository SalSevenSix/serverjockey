<script>
  let { data } = $props();

  function version() {
    return data.s.details.version;
  }
</script>


<div id="InstanceStatus" class="dashcontainer"><div class="dashpanel statbox is-{data.s.running ? 'green' : 'red'}">
  <div>
    <h2>Server Status</h2>
    <table><tbody>
      <tr><th>State</th><td>{data.s.state}</td></tr>
      {#if data.s.details}
        <tr><th>Version</th><td>
          {data.s.details.version ? data.s.details.version : '---'}
        </td></tr>
        <tr><th>Connect</th><td>
          {#if data.s.details.ip && data.s.details.port}
            <a href="steam://connect/{data.s.details.ip}:{data.s.details.port}">
              {data.s.details.ip}:{data.s.details.port}</a>
          {:else}
            ---
          {/if}
        </td></tr>
        {#if data.s.details.ingametime}
          <tr><th>Ingame</th><td>{data.s.details.ingametime}</td></tr>
        {/if}
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
