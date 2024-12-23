<script>
  import { getContext } from 'svelte';
  import { isBoolean } from '$lib/util/util';
  import { notifyInfo, notifyError } from '$lib/util/notifications';
  import { newPostRequest } from '$lib/util/sjgmsapi';
  import DropdownButton from '$lib/widget/DropdownButton.svelte';

  const instance = getContext('instance');
  const serverStatus = getContext('serverStatus');

  export let canRestartAfterWarnings = false;
  export let canRestartOnEmpty = false;

  $: transientState = $serverStatus.running && $serverStatus.state === 'STOPPED';
  $: cannotStop = !$serverStatus.running || $serverStatus.state === 'STOPPING' || transientState;
  $: cannotRestart = !$serverStatus.running || $serverStatus.state != 'STARTED';
  $: cannotStart = !isBoolean($serverStatus.running) || $serverStatus.running || $serverStatus.state === 'MAINTENANCE';

  function sendCommand(value, successMessage = null) {
    fetch(instance.url('/server/' + value), newPostRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        if (successMessage) { notifyInfo(successMessage); }
      })
      .catch(function(error) { notifyError('Failed to send server command.'); });
  }

  let restartOptions = null;
  if (canRestartAfterWarnings || canRestartOnEmpty) {
    restartOptions = [{ label: 'Immediately', onSelect: function() { sendCommand('restart-immediately'); }}];
    if (canRestartAfterWarnings) {
      restartOptions.push({ label: 'After Warnings', onSelect: function() {
        sendCommand('restart-after-warnings', 'Server restarting after warning players.'); }});
    }
    if (canRestartOnEmpty) {
      restartOptions.push({ label: 'On Empty', onSelect: function() {
        sendCommand('restart-on-empty', 'Server restarting when empty.'); }});
    }
  }
</script>


<div class="block buttons">
  <button id="serverControlsStop" class="button is-danger"
          on:click={function() { sendCommand('stop'); }} disabled={cannotStop}>
    <i class="fa fa-stop fa-lg"></i>&nbsp;&nbsp;Stop</button>
  {#if restartOptions}
    <DropdownButton id="serverControlsRestart" options={restartOptions} disabled={cannotRestart}>
      <i class="fa fa-arrows-rotate fa-lg"></i>&nbsp;&nbsp;Restart
    </DropdownButton>
  {:else}
    <button id="serverControlsRestart" class="button is-warning"
            on:click={function() { sendCommand('restart'); }} disabled={cannotRestart}>
      <i class="fa fa-arrows-rotate fa-lg"></i>&nbsp;&nbsp;Restart</button>
  {/if}
  <button id="serverControlsStart" class="button is-primary"
          on:click={function() { sendCommand('start'); }} disabled={cannotStart}>
    <i class="fa fa-play fa-lg"></i>&nbsp;&nbsp;Start</button>
</div>
