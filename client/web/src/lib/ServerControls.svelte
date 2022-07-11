<script>
	import { instance, serverStatus, postServerCommand } from '$lib/serverjockeyapi';

	function executeCommand() {
	  postServerCommand($instance, this.name);
	}
</script>

<div class="block">
  <button id="daemon" name="daemon" class="button is-success" disabled={$serverStatus.running} on:click={executeCommand}>Daemon</button>
  <button id="start" name="start" class="button is-primary" disabled={$serverStatus.running} on:click={executeCommand}>Start</button>
  <button id="restart" name="restart" class="button is-warning" disabled={!$serverStatus.running} on:click={executeCommand}>Restart</button>
  <button id="stop" name="stop" class="button is-danger" disabled={!$serverStatus.running} on:click={executeCommand}>Stop</button>
</div>
