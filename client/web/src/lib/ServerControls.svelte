<script>
  import { notifyError } from '$lib/notifications';
  import { instance, serverStatus, newPostRequest } from '$lib/serverjockeyapi';

  function executeCommand() {
    fetch($instance.url + '/server/' + this.name, newPostRequest())
      .then(function(response) { if (!response.ok) throw new Error('Status: ' + response.status); })
      .catch(function(error) { notifyError('Failed to send server command.'); });
  }
</script>


<div class="block buttons">
  <button name="stop" class="button is-danger" on:click={executeCommand}
          disabled={!$serverStatus.running || $serverStatus.state === 'STOPPING'}>
          Stop</button>
  <button name="restart" class="button is-warning" on:click={executeCommand}
          disabled={!$serverStatus.running || $serverStatus.state != 'STARTED'}>
          Restart</button>
  <button name="start" class="button is-primary" on:click={executeCommand}
          disabled={$serverStatus.running || $serverStatus.state === 'MAINTENANCE'}>
          Start</button>
  <button name="daemon" class="button is-success" on:click={executeCommand}
          disabled={$serverStatus.running || $serverStatus.state === 'MAINTENANCE'}>
          Daemon</button>
</div>
