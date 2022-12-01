<script>
  import Instance from '$lib/Instance.svelte';
  import Collapsible from '$lib/Collapsible.svelte';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
  import ConsoleLog from '$lib/ConsoleLog.svelte';
  import FileSystem from '$lib/FileSystem.svelte';
  import ConfigFile from '$lib/ConfigFile.svelte';
  import InstallRuntime from '$lib/InstallRuntime.svelte';
  import DeploymentActions from '$lib/DeploymentActions.svelte';
  import BackupRestoreActions from '$lib/BackupRestoreActions.svelte';

  let deploymentActions = {
    'wipe-world-save': 'Reset the game world map only.',
    'wipe-world-all': 'Reset game world map and configuration.'
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
          <p>No Players Component yet</p>
        </div>
      </div>
      <Collapsible title="Logging">
        <ConsoleLog />
        <FileSystem allowDelete />
      </Collapsible>
      <Collapsible title="Configuration">
        <div class="content">
          <p>For help with configuration, see the
             <a href="https://github.com/SmartlyDressedGames/U3-Docs/blob/master/ServerHosting.md#How-to-Install-SteamCMD-on-Linux"
                target="_blank">dedicated server guide</a> on github.</p>
        </div>
        <ConfigFile name="Command Line Args" path="/config/cmdargs" />
        <ConfigFile name="Server Commands" path="/config/commands" />
        <ConfigFile name="General Settings" path="/config/settings" />
        <ConfigFile name="Workshop Mods" path="/config/workshop" />
      </Collapsible>
      <Collapsible title="Deployment">
        <InstallRuntime qualifierName="Beta" showLog />
        <DeploymentActions actions={deploymentActions} />
      </Collapsible>
      <Collapsible title="Backups">
        <BackupRestoreActions />
      </Collapsible>
      <hr />
    </div>
  </div>
</Instance>
