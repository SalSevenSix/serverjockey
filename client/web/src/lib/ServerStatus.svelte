<script>
  import { onDestroy, getContext } from 'svelte';
  import { capitalize, humanDuration } from '$lib/util';
  import SpinnerIcon from '$lib/SpinnerIcon.svelte';

  const serverStatus = getContext('serverStatus');
  const commonKeys = ['version', 'ip', 'port'];

  export let stateOnly = false;

  $: uptime = $serverStatus.uptime ? $serverStatus.uptime : 0;
  let uptimeClock = setInterval(function() { uptime += 10000; }, 10000);

  onDestroy(function() {
    clearInterval(uptimeClock);
  });
</script>


<div class="block">
  <table class="table">
    <tbody>
      <tr><td class="has-text-weight-bold">State</td><td>
        {#if $serverStatus.state}
          {#if $serverStatus.running}
            <i class="fa fa-toggle-on ss-running fa-lg"></i>
          {:else}
            <i class="fa {$serverStatus.state === 'MAINTENANCE' ? 'fa-toggle-on ss-maint' : 'fa-toggle-off'} fa-lg"></i>
          {/if}
          &nbsp;{$serverStatus.state}
          {#if $serverStatus.state === 'STARTED'}({humanDuration(uptime)}){/if}
        {:else}
          <SpinnerIcon /> ...
        {/if}
      </td></tr>
      {#if !stateOnly}
        {#if $serverStatus.details}
          <tr><td class="has-text-weight-bold">Version</td><td>
            {$serverStatus.details.version ? $serverStatus.details.version : ''}
          </td></tr>
          <tr><td class="has-text-weight-bold">Connect</td><td>
            {$serverStatus.details.ip ? $serverStatus.details.ip : ''}{$serverStatus.details.ip && $serverStatus.details.port ? ':' : ''}{$serverStatus.details.port ? $serverStatus.details.port : ''}
          </td></tr>
        {:else}
          <tr><td class="has-text-weight-bold">Version</td><td></td></tr>
          <tr><td class="has-text-weight-bold">Connect</td><td></td></tr>
        {/if}
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
