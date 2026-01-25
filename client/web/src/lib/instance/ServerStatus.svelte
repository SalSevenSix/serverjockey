<script>
  import { onDestroy, getContext } from 'svelte';
  import { hasProp, humanDuration } from 'common/util/util';
  import { capitalize } from '$lib/util/util';
  import { newPostRequest } from '$lib/util/sjgmsapi';
  import { notifyInfo, notifyError } from '$lib/util/notifications';
  import SpinnerIcon from '$lib/widget/SpinnerIcon.svelte';
  import ExtLink from '$lib/widget/ExtLink.svelte';
  import ServerStateSymbol from '$lib/widget/ServerStateSymbol.svelte';

  const instance = getContext('instance');
  const serverStatus = getContext('serverStatus');

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

  $: extras = getDetails($serverStatus.details); function getDetails(details) {
    const result = [];
    if (!details) return result;
    const excludedKeys = ['version', 'ip', 'port'];
    for (const [key, detail] of Object.entries(details)) {
      if (!excludedKeys.includes(key)) {
        const entry = { type: 'text', label: capitalize(key), value: detail, data: null };
        if (hasProp(detail, 'type')) {
          entry.type = detail.type;
          if (hasProp(detail, 'label')) { entry.label = detail.label; }
          if (hasProp(detail, 'value')) { entry.value = detail.value; }
          if (hasProp(detail, 'data')) { entry.data = detail.data; }
        }
        result.push(entry);
      }
    }
    return result;
  }

  $: uptime = $serverStatus.uptime ? $serverStatus.uptime : 0;
  const uptimeClock = setInterval(function() { uptime += 10000; }, 10000);

  function sendCommand(cmd) {
    const request = newPostRequest();
    request.body = JSON.stringify({ 'line': cmd });
    fetch(instance.url('/console/send'), request)
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        notifyInfo('Console command sent.');
      })
      .catch(function() {
        notifyError('Failed to send command to server.');
      });
  }

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
      {#each extras as entry}
        <tr>
          <td class="has-text-weight-bold">{entry.label}</td>
          <td id="serverStatus{entry.label}">
            {#if entry.type === 'cmd'}
               <button id="serverStatus{entry.label}Cmd" class="button button-cmd is-success"
                 on:click={function() { sendCommand(entry.data); }}>{entry.value}</button>
            {:else if entry.type === 'url'}
              <ExtLink id="serverStatus{entry.label}Url" href={entry.data}>{entry.value}</ExtLink>
            {:else}
              {entry.value}
            {/if}
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>


<style>
  .full-size-status {
    min-height: 8.5em;
  }

  .button-cmd {
    height: 1.6em;
  }
</style>
