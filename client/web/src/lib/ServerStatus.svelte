<script>
  import { capitalize, humanDuration } from '$lib/util';
  import { serverStatus } from '$lib/serverjockeyapi';
</script>


<div class="block">
  <table class="table">
    <tbody>
      <tr><td class="has-text-weight-bold">Running</td><td>{$serverStatus.running}</td></tr>
      {#if $serverStatus.state}
        <tr><td class="has-text-weight-bold">State</td><td>{$serverStatus.state}</td></tr>
      {/if}
      {#if $serverStatus.uptime}
        <tr><td class="has-text-weight-bold">Uptime</td><td>{humanDuration($serverStatus.uptime)}</td></tr>
      {/if}
      {#if $serverStatus.details}
        {#each Object.keys($serverStatus.details) as key}
          <tr><td class="has-text-weight-bold">{capitalize(key)}</td><td>{$serverStatus.details[key]}</td></tr>
        {/each}
      {/if}
    </tbody>
  </table>
</div>
