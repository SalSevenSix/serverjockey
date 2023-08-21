<script>
  import ServerStatusStore from '$lib/ServerStatusStore.svelte';
  import Instance from '$lib/Instance.svelte';
  import Collapsible from '$lib/Collapsible.svelte';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerConfig from '$lib/ServerConfig.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
  import Players from '$lib/Players.svelte';
  import InstanceLog from '$lib/InstanceLog.svelte';
  import LogFiles from '$lib/LogFiles.svelte';
  import ConfigFile from '$lib/ConfigFile.svelte';
  import InstallRuntime from '$lib/InstallRuntime.svelte';
  import DeploymentActions from '$lib/DeploymentActions.svelte';
  import BackupRestoreActions from '$lib/BackupRestoreActions.svelte';
  import CommandBuilder from '$lib/CommandBuilder.svelte';

  let deploymentActions = [
    { 'key': 'wipe-world-save', 'name': 'World Save',
      'desc': 'Reset the game world map only.' },
    { 'key': 'wipe-world-all', 'name': 'World All', 'icon': 'fa-explosion',
      'desc': 'Reset game world map and configuration.' }];

  let consoleCommands = {
    'console': {
      'send': [
        {name: 'help', input: 'display'},
        {name: 'line', input: 'text>', type: 'string'}
      ]
    }
  };
</script>


<ServerStatusStore><Instance>
  <div class="columns">
    <div class="column">
      <div class="columns">
        <div class="column">
          <ServerControls />
          <ServerConfig />
        </div>
        <div class="column">
          <ServerStatus />
        </div>
      </div>
      <InstanceLog />
      <Collapsible icon="fa-keyboard" title="Console Commands">
        <CommandBuilder commands={consoleCommands} />
      </Collapsible>
      <Collapsible icon="fa-user" title="Players">
        <Players />
      </Collapsible>
      <Collapsible icon="fa-file-code" title="Configuration">
        <div class="content">
          <p>For help with configuration, see the
          <a href="https://docs.smartlydressedgames.com/en/stable/servers/server-hosting.html#how-to-configure-server"
             target="_blank">server guide <i class="fa fa-up-right-from-square"></i></a> on the docs website.<br />
          Default configuration files are not generated until after first server start.</p>
        </div>
        <ConfigFile name="Command Line Args" path="/config/cmdargs" />
        <ConfigFile name="Server Commands" path="/config/commands" />
        <ConfigFile name="General Settings" path="/config/settings" />
        <ConfigFile name="Workshop Mods" path="/config/workshop" />
      </Collapsible>
      <Collapsible icon="fa-scroll" title="Logging">
        <LogFiles />
      </Collapsible>
      <Collapsible icon="fa-gears" title="Deployment">
        <InstallRuntime qualifierName="Beta (optional)" />
        <DeploymentActions actions={deploymentActions} />
      </Collapsible>
      <Collapsible icon="fa-box-archive" title="Backups">
        <BackupRestoreActions />
      </Collapsible>
    </div>
  </div>
</Instance></ServerStatusStore>
