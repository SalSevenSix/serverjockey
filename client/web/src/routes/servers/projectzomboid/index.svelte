<script>
  import Instance from '$lib/Instance.svelte';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
  import Players from '$lib/Players.svelte';
  import ConsoleLog from '$lib/ConsoleLog.svelte';
  import FileSystem from '$lib/FileSystem.svelte';
  import ConfigFile from '$lib/ConfigFile.svelte';
  import InstallRuntime from '$lib/InstallRuntime.svelte';
  import DeploymentActions from '$lib/DeploymentActions.svelte';
  import BackupRestoreActions from '$lib/BackupRestoreActions.svelte';

  let deploymentActions = {
    'wipe-world-save': 'Reset the game world save only.',
    'wipe-world-playerdb': 'Reset the player database only.',
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
      <hr />
      <h2 class="title is-5">Logging</h2>
      <ConsoleLog />
      <FileSystem />
      <hr />
      <h2 class="title is-5">Configuration</h2>
      <ConfigFile name="INI Settings" path="/config/ini" />
      <ConfigFile name="Sandbox Settings" path="/config/sandbox" />
      <ConfigFile name="Spawn Regions" path="/config/spawnregions" />
      <ConfigFile name="Spawn Points" path="/config/spawnpoints" />
      <ConfigFile name="JRE Settings" path="/config/jvm" />
      <hr />
      <h2 class="title is-5">Deployment</h2>
      <InstallRuntime qualifierName="Beta" showLog />
      <DeploymentActions actions={deploymentActions} />
      <hr />
      <h2 class="title is-5">Backups</h2>
      <BackupRestoreActions />
      <hr />
    </div>
  </div>
</Instance>
