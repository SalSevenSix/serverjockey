<script>
  import ServerStatusStore from '$lib/ServerStatusStore.svelte';
  import Instance from '$lib/Instance.svelte';
  import Collapsible from '$lib/Collapsible.svelte';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerConfig from '$lib/ServerConfig.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
  import InstanceLog from '$lib/InstanceLog.svelte';
  import Players from '$lib/Players.svelte';
  import ConfigFile from '$lib/ConfigFile.svelte';
  import LogFiles from '$lib/LogFiles.svelte';
  import InstallRuntime from '$lib/InstallRuntime.svelte';
  import DeploymentActions from '$lib/DeploymentActions.svelte';
  import BackupRestoreActions from '$lib/BackupRestoreActions.svelte';
  import CommandBuilder from '$lib/CommandBuilder.svelte';
  import CheckStore from '$lib/CheckStore.svelte';
  import InstanceActivity from '$lib/InstanceActivity.svelte';
  import PlayerActivity from '$lib/PlayerActivity.svelte';
  import ChatActivity from '$lib/ChatActivity.svelte';

  const deploymentActions = [
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
        <InstallRuntime qualifierName="Version (optional)" />
        <DeploymentActions actions={deploymentActions} />
      </Collapsible>
      <Collapsible icon="fa-box-archive" title="Backups">
        <BackupRestoreActions />
      </Collapsible>
      <CheckStore>
        <Collapsible icon="fa-chart-pie" title="Activity">
          <InstanceActivity />
          <PlayerActivity />
        </Collapsible>
        <Collapsible icon="fa-comments" title="Chat Log">
          <ChatActivity />
        </Collapsible>
      </CheckStore>
    </div>
  </div>
</Instance></ServerStatusStore>
