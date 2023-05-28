<script>
  import { notifyError } from '$lib/notifications';
  import { instance, serverStatus, newPostRequest } from '$lib/sjgmsapi';

  function executeCommand() {
    fetch($instance.url + '/server/' + this.name, newPostRequest())
      .then(function(response) { if (!response.ok) throw new Error('Status: ' + response.status); })
      .catch(function(error) { notifyError('Failed to send server command.'); });
  }
</script>


<div class="block buttons">
  <button name="stop" title="Stop" class="button is-danger" on:click={executeCommand}
          disabled={!$serverStatus.running || $serverStatus.state === 'STOPPING'}>
          <i class="fa fa-stop fa-lg"></i>&nbsp;&nbsp;Stop</button>
  <button name="restart" title="Restart" class="button is-warning" on:click={executeCommand}
          disabled={!$serverStatus.running || $serverStatus.state != 'STARTED'}>
          <i class="fa fa-arrows-rotate fa-lg"></i>&nbsp;&nbsp;Restart</button>
  <button name="start" title="Start" class="button is-primary" on:click={executeCommand}
          disabled={$serverStatus.running || $serverStatus.state === 'MAINTENANCE'}>
          <i class="fa fa-play fa-lg"></i>&nbsp;&nbsp;Start</button>
</div>
