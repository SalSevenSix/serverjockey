<script>
  import { capitalize, humanDuration } from '$lib/util';
  import { serverStatus } from '$lib/serverjockeyapi';

  export let stateOnly = false;
  let commonKeys = ['version', 'ip', 'port'];
</script>


<div class="block">
  <table class="table">
    <tbody>
      <tr><td class="has-text-weight-bold">State</td><td>
        {#if $serverStatus.running}
          <i class="fa fa-toggle-on ss-running fa-lg"></i>
        {:else}
          <i class="fa {$serverStatus.state === 'MAINTENANCE' ? 'fa-toggle-on ss-maint' : 'fa-toggle-off'} fa-lg"></i>
        {/if}
        &nbsp;{$serverStatus.state}
        {#if $serverStatus.state === 'STARTED' && $serverStatus.uptime}
          ({humanDuration($serverStatus.uptime)})
        {/if}
      </td></tr>
      {#if !stateOnly}
        <tr><td class="has-text-weight-bold">Version</td><td>
          {#if $serverStatus.details}
            {$serverStatus.details.version ? $serverStatus.details.version : ''}
          {/if}
        </td></tr>
        <tr><td class="has-text-weight-bold">Connect</td><td>
          {#if $serverStatus.details}
            {$serverStatus.details.ip ? $serverStatus.details.ip : ''}{$serverStatus.details.ip && $serverStatus.details.port ? ':' : ''}{$serverStatus.details.port ? $serverStatus.details.port : ''}
          {/if}
        </td></tr>
      {/if}
      {#if $serverStatus.details}
        {#each Object.keys($serverStatus.details) as key}
          {#if !commonKeys.includes(key)}
            <tr><td class="has-text-weight-bold">{capitalize(key)}</td><td>{$serverStatus.details[key]}</td></tr>
          {/if}
        {/each}
      {/if}
    </tbody>
  </table>
</div>


<style>
  .ss-running {
    color: #48C78E;
  }
  .ss-maint {
    color: #F14668;
  }
</style>
