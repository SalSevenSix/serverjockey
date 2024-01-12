<script>
  import { getContext } from 'svelte';
  import { isBoolean } from '$lib/util/util';
  import { notifyError } from '$lib/util/notifications';
  import { newPostRequest } from '$lib/util/sjgmsapi';

  const instance = getContext('instance');
  const serverStatus = getContext('serverStatus');

  $: transientState = $serverStatus.running && $serverStatus.state === 'STOPPED';
  $: cannotStop = !$serverStatus.running || $serverStatus.state === 'STOPPING' || transientState;
  $: cannotRestart = !$serverStatus.running || $serverStatus.state != 'STARTED';
  $: cannotStart = !isBoolean($serverStatus.running) || $serverStatus.running || $serverStatus.state === 'MAINTENANCE';

  function doCommand() {
    fetch(instance.url('/server/' + this.name), newPostRequest())
      .then(function(response) { if (!response.ok) throw new Error('Status: ' + response.status); })
      .catch(function(error) { notifyError('Failed to send server command.'); });
  }
</script>


<div class="block buttons">
  <button name="stop" title="Stop" class="button is-danger" on:click={doCommand} disabled={cannotStop}>
    <i class="fa fa-stop fa-lg"></i>&nbsp;&nbsp;Stop</button>
  <button name="restart" title="Restart" class="button is-warning" on:click={doCommand} disabled={cannotRestart}>
    <i class="fa fa-arrows-rotate fa-lg"></i>&nbsp;&nbsp;Restart</button>
  <button name="start" title="Start" class="button is-primary" on:click={doCommand} disabled={cannotStart}>
    <i class="fa fa-play fa-lg"></i>&nbsp;&nbsp;Start</button>
</div>
