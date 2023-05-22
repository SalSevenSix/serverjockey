<script>
  import { capitalize, humanDuration } from '$lib/util';
  import { serverStatus } from '$lib/serverjockeyapi';
  import ServerStatusToggle from '$lib/ServerStatusToggle.svelte';
</script>


<div class="block">
  <table class="table">
    <tbody>
      {#if $serverStatus.state}
        <tr><td class="has-text-weight-bold">State</td><td>
          <ServerStatusToggle />&nbsp;{$serverStatus.state}
        </td></tr>
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
