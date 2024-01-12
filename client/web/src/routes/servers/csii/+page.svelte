<script>
  import Collapsible from '$lib/widget/Collapsible.svelte';
  import ServerStatusStore from '$lib/instance/ServerStatusStore.svelte';
  import InstanceHeader from '$lib/instance/InstanceHeader.svelte';
  import ServerStatus from '$lib/instance/ServerStatus.svelte';
  import ServerConfig from '$lib/instance/ServerConfig.svelte';
  import ServerControls from '$lib/instance/ServerControls.svelte';
  import InstanceLog from '$lib/instance/InstanceLog.svelte';
  import Players from '$lib/instance/Players.svelte';
  import ConfigFile from '$lib/instance/ConfigFile.svelte';
  import LogFiles from '$lib/instance/LogFiles.svelte';
  import RuntimeControls from '$lib/instance/RuntimeControls.svelte';
  import WorldControls from '$lib/instance/WorldControls.svelte';
  import BackupRestoreActions from '$lib/instance/BackupRestoreActions.svelte';
  import CommandBuilder from '$lib/instance/CommandBuilder.svelte';
  import StoreInstance from '$lib/instance/StoreInstance.svelte';

  const worldActions = [
    { 'key': 'wipe-world-all', 'name': 'Reset All', 'icon': 'fa-explosion',
      'desc': 'Reset all configuration and delete all logs.' }];

  const consoleCommands = {
    'console': {
      'send': [
        {name: 'help', input: 'display'},
        {name: 'line', input: 'text>', type: 'string'}
      ]
    }
  };
</script>


<ServerStatusStore>
  <InstanceHeader />
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
        <ConfigFile name="Command Line Args" path="/config/cmdargs">
          <p>
            See &quot;_comment_...&quot; fields for description of configuration fields.
            Additional launch options can be added. Fields starting with an underscore
            and the &quot;upnp&quot; field are ignored as launch options.
          </p>
        </ConfigFile>
        <ConfigFile name="Server" path="/config/server" />
        <ConfigFile name="Competitive" path="/config/gamemode-competitive" />
        <ConfigFile name="Wingman" path="/config/gamemode-wingman" />
        <ConfigFile name="Casual" path="/config/gamemode-casual" />
        <ConfigFile name="Deathmatch" path="/config/gamemode-deathmatch" />
        <ConfigFile name="Custom" path="/config/gamemode-custom" />
      </Collapsible>
      <Collapsible icon="fa-scroll" title="Logging">
        <LogFiles allowDelete={1} />
      </Collapsible>
      <Collapsible icon="fa-gears" title="Deployment">
        <RuntimeControls qualifierName="Beta" />
        <WorldControls actions={worldActions} />
      </Collapsible>
      <Collapsible icon="fa-box-archive" title="Backups">
        <BackupRestoreActions />
      </Collapsible>
      <StoreInstance />
    </div>
  </div>
</ServerStatusStore>
