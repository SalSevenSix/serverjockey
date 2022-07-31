<script>
  import Instance from '$lib/Instance.svelte';
  import Collapsible from '$lib/Collapsible.svelte';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
  import Players from '$lib/Players.svelte';
  import ConsoleLog from '$lib/ConsoleLog.svelte';
  import ConfigFile from '$lib/ConfigFile.svelte';
  import InstallRuntime from '$lib/InstallRuntime.svelte';
  import DeploymentActions from '$lib/DeploymentActions.svelte';
  import BackupRestoreActions from '$lib/BackupRestoreActions.svelte';

  let deploymentActions = {
    'wipe-world-save': 'Reset the game world save only.',
    'wipe-world-config': 'Reset the configuration files only.',
    'wipe-world-all': 'Reset all of the above.'
  };
</script>


<Instance>
  <div class="columns">
    <div class="column">
      <div class="columns">
        <div class="column">
          <ServerControls />
          <ServerStatus />
        </div>
        <div class="column">
          <Players />
        </div>
      </div>
      <Collapsible title="Logging">
        <ConsoleLog />
      </Collapsible>
      <Collapsible title="Configuration">
        <ConfigFile name="Command Line Args" path="/config/cmdargs" />
        <ConfigFile name="Server" path="/config/server" />
        <ConfigFile name="Map" path="/config/map" />
        <ConfigFile name="Map Gen" path="/config/mapgen" />
        <ConfigFile name="Mods List" path="/config/modslist" />
        <ConfigFile name="Admin List" path="/config/adminlist" />
        <ConfigFile name="White List" path="/config/whitelist" />
        <ConfigFile name="Ban List" path="/config/banlist" />
      </Collapsible>
      <Collapsible title="Deployment">
        <InstallRuntime />
        <DeploymentActions actions={deploymentActions} />
      </Collapsible>
      <Collapsible title="Backups">
        <BackupRestoreActions />
      </Collapsible>
      <hr />
    </div>
  </div>
</Instance>
