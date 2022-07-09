<script>
	import { instance, serverStatus, postServerCommand } from '$lib/serverjockeyapi';

	function executeCommand() {
	  postServerCommand($instance, this.name);
	}
</script>


<div>
  <button id="daemon" name="daemon" disabled={$serverStatus.running} on:click={executeCommand}>Daemon</button>
  <button id="start" name="start" disabled={$serverStatus.running} on:click={executeCommand}>Start</button>
  <button id="restart" name="restart" disabled={!$serverStatus.running} on:click={executeCommand}>Restart</button>
  <button id="stop" name="stop" disabled={!$serverStatus.running} on:click={executeCommand}>Stop</button>
</div>
