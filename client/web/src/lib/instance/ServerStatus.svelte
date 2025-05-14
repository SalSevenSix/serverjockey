<script>
  import { onDestroy, getContext } from 'svelte';
  import { humanDuration } from 'common/util/util';
  import { capitalize } from '$lib/util/util';
  import SpinnerIcon from '$lib/widget/SpinnerIcon.svelte';
  import ServerStateSymbol from '$lib/widget/ServerStateSymbol.svelte';

  const serverStatus = getContext('serverStatus');
  const commonKeys = ['version', 'ip', 'port'];

  export let stateOnly = false;

  $: version = $serverStatus.details && $serverStatus.details.version ? $serverStatus.details.version : '';

  $: connect = getConnect($serverStatus.details); function getConnect(details) {
    const result = { ip: '', port: '', url: null };
    if (!details) return result;
    if (details.ip) { result.ip = details.ip; }
    if (details.port) { result.port = details.port; }
    if (result.ip && result.port) { result.url = 'steam://connect/' + result.ip + ':' + result.port; }
    return result;
  }

  $: uptime = $serverStatus.uptime ? $serverStatus.uptime : 0;
  const uptimeClock = setInterval(function() { uptime += 10000; }, 10000);

  onDestroy(function() {
    clearInterval(uptimeClock);
  });
</script>


<div class="block" class:full-size-status={!stateOnly}>
  <table class="table">
    <tbody>
      <tr><td class="has-text-weight-bold">State</td><td id="serverStatusState">
        {#if $serverStatus.state}
          <ServerStateSymbol state={$serverStatus.state} />&nbsp; {$serverStatus.state}
          {#if $serverStatus.state === 'STARTED'}
            <span class="notranslate">({humanDuration(uptime)})</span>
          {/if}
        {:else}
          <SpinnerIcon /> ...
        {/if}
      </td></tr>
      {#if !stateOnly}
        <tr><td class="has-text-weight-bold">Version</td>
            <td id="serverStatusVersion">{version}</td></tr>
        <tr><td class="has-text-weight-bold">Connect</td>
            <td id="serverStatusConnect">
              {#if connect.ip}{connect.ip}{/if}{#if connect.url}<wbr>:{/if}{#if connect.port}{connect.port}{/if}
              {#if connect.url}<a href={connect.url} title="Play through Steam"><i class="fa-brands fa-steam"></i></a>{/if}
            </td></tr>
      {/if}
      {#if $serverStatus.details}
        {#each Object.keys($serverStatus.details) as key}
          {#if !commonKeys.includes(key)}
            <tr><td class="has-text-weight-bold">{capitalize(key)}</td>
                <td id="serverStatus{capitalize(key)}">{$serverStatus.details[key]}</td></tr>
          {/if}
        {/each}
      {/if}
    </tbody>
  </table>
</div>


<style>
  .full-size-status {
    min-height: 8.5em;
  }
</style>
