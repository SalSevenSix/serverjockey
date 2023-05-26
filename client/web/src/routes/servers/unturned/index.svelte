<script>
  import Instance from '$lib/Instance.svelte';
  import Collapsible from '$lib/Collapsible.svelte';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerConfig from '$lib/ServerConfig.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
  import Players from '$lib/Players.svelte';
  import ConsoleLog from '$lib/ConsoleLog.svelte';
  import FileSystem from '$lib/FileSystem.svelte';
  import ConfigFile from '$lib/ConfigFile.svelte';
  import InstallRuntime from '$lib/InstallRuntime.svelte';
  import DeploymentActions from '$lib/DeploymentActions.svelte';
  import BackupRestoreActions from '$lib/BackupRestoreActions.svelte';
  import CommandBuilder from '$lib/CommandBuilder.svelte';

  let deploymentActions = [
    { 'key': 'wipe-world-save', 'icon': 'explosion', 'name': 'World Save',
      'desc': 'Reset the game world map only.' },
    { 'key': 'wipe-world-all', 'icon': 'explosion', 'name': 'World All',
      'desc': 'Reset game world map and configuration.' }];

  let consoleCommands = {
    'console': {
      'send': [
        {name: 'help', input: 'display'},
        {name: 'line', input: 'text', type: 'string'}
      ]
    }
  };
</script>


<Instance>
  <div class="columns">
    <div class="column">
      <div class="columns">
        <div class="column">
          <ServerControls />
          <ServerConfig />
          <ServerStatus />
        </div>
        <div class="column">
          <Players />
        </div>
      </div>
      <ConsoleLog />
      <Collapsible title="Console Commands">
        <CommandBuilder commands={consoleCommands} />
      </Collapsible>
      <Collapsible title="Configuration">
        <div class="content">
          <p>For help with configuration, see the
          <a href="https://github.com/SmartlyDressedGames/U3-Docs/blob/master/ServerHosting.md#How-to-Configure-Server"
             target="_blank">dedicated server guide</a> on github.<br />
          Default configuration files are not generated until after first server start.</p>
        </div>
        <ConfigFile name="Command Line Args" path="/config/cmdargs" />
        <ConfigFile name="Server Commands" path="/config/commands" />
        <ConfigFile name="General Settings" path="/config/settings" />
        <ConfigFile name="Workshop Mods" path="/config/workshop" />
      </Collapsible>
      <Collapsible title="Logging">
        <FileSystem allowDelete />
      </Collapsible>
      <Collapsible title="Deployment">
        <InstallRuntime qualifierName="Beta (optional)" />
        <DeploymentActions actions={deploymentActions} />
      </Collapsible>
      <Collapsible title="Backups">
        <BackupRestoreActions />
      </Collapsible>
    </div>
  </div>
</Instance>
