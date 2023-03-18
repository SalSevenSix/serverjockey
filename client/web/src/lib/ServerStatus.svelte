<script>
  import { capitalize, humanDuration } from '$lib/util';
  import { serverStatus } from '$lib/serverjockeyapi';
</script>


<div class="block">
  <table class="table">
    <tbody>
      <tr><td><strong>Running</strong></td><td>{$serverStatus.running}</td></tr>
      {#if $serverStatus.state}
        <tr><td><strong>State</strong></td><td>{$serverStatus.state}</td></tr>
      {/if}
      {#if $serverStatus.uptime}
        <tr><td><strong>Uptime</strong></td><td>{humanDuration($serverStatus.uptime)}</td></tr>
      {/if}
      {#if $serverStatus.details}
        {#each Object.keys($serverStatus.details) as key}
          <tr><td><strong>{capitalize(key)}</strong></td><td>{$serverStatus.details[key]}</td></tr>
        {/each}
      {/if}
    </tbody>
  </table>
</div>
