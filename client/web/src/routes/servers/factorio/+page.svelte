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
    { 'key': 'wipe-world-save', 'name': 'World Save',
      'desc': 'Reset the game world save only.' },
    { 'key': 'wipe-world-config', 'name': 'World Config',
      'desc': 'Reset the configuration files only.' },
    { 'key': 'wipe-world-all', 'name': 'World All', 'icon': 'fa-explosion',
      'desc': 'Reset all of the above.' }];

  let consoleCommands = {
    'console': {
      'send': [
        {name: 'help', input: 'display'},
        {name: 'line', input: 'text>', type: 'string'}
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
      <ConsoleLog hasConsoleLogFile />
      <Collapsible icon="fa-keyboard" title="Console Commands">
        <CommandBuilder commands={consoleCommands} />
      </Collapsible>
      <Collapsible icon="fa-file-code" title="Configuration">
        <ConfigFile name="Command Line Args" path="/config/cmdargs">
          <p>See &quot;_comment_...&quot; fields for description of configuration fields.</p>
        </ConfigFile>
        <ConfigFile name="Server" path="/config/server">
          <p>See &quot;_comment_...&quot; fields for description of configuration fields.</p>
        </ConfigFile>
        <ConfigFile name="Map" path="/config/map">
          <p>See &quot;_comment_...&quot; fields for description of configuration fields.</p>
        </ConfigFile>
        <ConfigFile name="Map Gen" path="/config/mapgen">
          <p>See &quot;_comment_...&quot; fields for description of configuration fields.</p>
        </ConfigFile>
        <ConfigFile name="Mods List" path="/config/modslist">
          <p>
            For automatic mod downloading you need to set both username and token in the
            <span class="has-text-weight-bold">Server</span> configuration.
            You can find these credentials in your player-data.json file in your Factorio profile.
            i.e. C:\Users\&lt;YOU&gt;\AppData\Roaming\Factorio\player-data.json
          </p>
        </ConfigFile>
        <ConfigFile name="Admin List" path="/config/adminlist">
          <p>List of user names to grant admin powers.
             e.g. [&quot;name1&quot;, &quot;name2&quot;]</p>
        </ConfigFile>
        <ConfigFile name="White List" path="/config/whitelist">
          <p>List of user names to allow access to the server if using whitelist.
             e.g. [&quot;name1&quot;, &quot;name2&quot;]</p>
        </ConfigFile>
        <ConfigFile name="Ban List" path="/config/banlist">
          <p>List of user names banned from server.
             e.g. [&quot;name1&quot;, &quot;name2&quot;]</p>
        </ConfigFile>
      </Collapsible>
      <Collapsible icon="fa-scroll" title="Logging">
        <FileSystem />
      </Collapsible>
      <Collapsible icon="fa-gears" title="Deployment">
        <InstallRuntime qualifierName="Version (optional)" />
        <DeploymentActions actions={deploymentActions} />
      </Collapsible>
      <Collapsible icon="fa-box-archive" title="Backups">
        <BackupRestoreActions />
      </Collapsible>
    </div>
  </div>
</Instance>