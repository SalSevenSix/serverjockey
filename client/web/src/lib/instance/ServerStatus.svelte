<script>
  import { onDestroy, getContext } from 'svelte';
  import { capitalize, humanDuration } from '$lib/util/util';
  import SpinnerIcon from '$lib/widget/SpinnerIcon.svelte';

  const serverStatus = getContext('serverStatus');
  const commonKeys = ['version', 'ip', 'port'];

  export let stateOnly = false;

  $: statusIconClass = getStatusIconClass($serverStatus.running, $serverStatus.state);
  function getStatusIconClass(running, state) {
    if (state === 'MAINTENANCE') return 'fa-toggle-on ss-maintenance';
    if (!running || !state) return 'fa-toggle-off';
    if (state === 'STARTED') return 'fa-toggle-on ss-started';
    return 'fa-toggle-on ss-working';
  }

  $: version = ($serverStatus.details && $serverStatus.details.version) ? $serverStatus.details.version : '';

  $: connect = getConnect($serverStatus.details);
  function getConnect(details) {
    if (!details) return '';
    let result = details.ip ? details.ip : '';
    if (details.ip && details.port) { result += ':'; }
    if (details.port) { result += details.port; }
    return result;
  }

  $: uptime = $serverStatus.uptime ? $serverStatus.uptime : 0;
  const uptimeClock = setInterval(function() { uptime += 10000; }, 10000);

  onDestroy(function() {
    clearInterval(uptimeClock);
  });
</script>


<div class="block">
  <table class="table">
    <tbody>
      <tr><td class="has-text-weight-bold">State</td><td>
        {#if $serverStatus.state}
          <i class="fa {statusIconClass} fa-lg"></i>&nbsp; {$serverStatus.state}
          {#if $serverStatus.state === 'STARTED'}
            <span class="notranslate">({humanDuration(uptime)})</span>
          {/if}
        {:else}
          <SpinnerIcon /> ...
        {/if}
      </td></tr>
      {#if !stateOnly}
        <tr><td class="has-text-weight-bold">Version</td><td>{version}</td></tr>
        <tr><td class="has-text-weight-bold">Connect</td><td>{connect}</td></tr>
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
  .ss-started {
    color: #48C78E;
  }

  .ss-working {
    color: #FFE08A;
  }

  .ss-maintenance {
    color: #F14668;
  }
</style>
