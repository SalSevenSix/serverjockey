<script>
  import Instance from '$lib/Instance.svelte';
  import Collapsible from '$lib/Collapsible.svelte';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
  import Players from '$lib/Players.svelte';
  import ConsoleLog from '$lib/ConsoleLog.svelte';
  import FileSystem from '$lib/FileSystem.svelte';
  import ConfigFile from '$lib/ConfigFile.svelte';
  import InstallRuntime from '$lib/InstallRuntime.svelte';
  import DeploymentActions from '$lib/DeploymentActions.svelte';
  import BackupRestoreActions from '$lib/BackupRestoreActions.svelte';
  import CommandBuilder from '$lib/CommandBuilder.svelte';

  let deploymentActions = {
    'wipe-world-save': 'Reset the game world map only.',
    'wipe-world-all': 'Reset game world map and configuration.'
  };

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
          <ServerStatus />
        </div>
        <div class="column">
          <Players />
        </div>
      </div>
      <ConsoleLog hasConsoleLogFile />
      <Collapsible title="Console Commands">
        <CommandBuilder commands={consoleCommands} />
      </Collapsible>
      <Collapsible title="Logging">
        <FileSystem allowDelete sortFunction={function(a, b) { return a.name.localeCompare(b.name); }} />
      </Collapsible>
      <Collapsible title="Configuration">
        <div class="content">
          <p>
            For help with configuration, see the
            <a href="https://starbounder.org/Guide:LinuxServerSetup#Configuration"
               target="_blank">dedicated server guide</a> on the Starbound wiki.<br />
            Default Settings file is not generated until after first server start.
          </p>
        </div>
        <ConfigFile name="Settings" path="/config/settings" />
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
