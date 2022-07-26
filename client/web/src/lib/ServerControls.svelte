<script>
	import { instance, serverStatus, newPostRequest } from '$lib/serverjockeyapi';

	function executeCommand() {
    fetch($instance.url + '/server/' + this.name, newPostRequest())
      .then(function(response) { if (!response.ok) throw new Error('Status: ' + response.status); })
      .catch(function(error) { alert('Error ' + error); });
	}
</script>


<div class="block buttons">
  <button id="servercontrols-stop" name="stop" class="button is-danger" disabled={!$serverStatus.running} on:click={executeCommand}>Stop</button>
  <button id="servercontrols-restart" name="restart" class="button is-warning" disabled={!$serverStatus.running} on:click={executeCommand}>Restart</button>
  <button id="servercontrols-start" name="start" class="button is-primary" disabled={$serverStatus.running} on:click={executeCommand}>Start</button>
  <button id="servercontrols-daemon" name="daemon" class="button is-success" disabled={$serverStatus.running} on:click={executeCommand}>Daemon</button>
</div>
