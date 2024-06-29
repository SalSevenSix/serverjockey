<script>
  import ExtLink from '$lib/widget/ExtLink.svelte';
  import Collapsible from '$lib/widget/Collapsible.svelte';
  import ServerStatusStore from '$lib/instance/ServerStatusStore.svelte';
  import InstanceHeader from '$lib/instance/InstanceHeader.svelte';
  import ServerStatus from '$lib/instance/ServerStatus.svelte';
  import ServerConfig from '$lib/instance/ServerConfig.svelte';
  import ServerControls from '$lib/instance/ServerControls.svelte';
  import Players from '$lib/instance/Players.svelte';
  import InstanceLog from '$lib/instance/InstanceLog.svelte';
  import LogFiles from '$lib/instance/LogFiles.svelte';
  import ConfigFile from '$lib/instance/ConfigFile.svelte';
  import RuntimeControls from '$lib/instance/RuntimeControls.svelte';
  import WorldControls from '$lib/instance/WorldControls.svelte';
  import BackupRestoreActions from '$lib/instance/BackupRestoreActions.svelte';
  import CommandBuilder from '$lib/instance/CommandBuilder.svelte';
  import StoreInstance from '$lib/instance/StoreInstance.svelte';

  const worldActions = [
    { 'key': 'wipe-world-save', 'name': 'Reset Save',
      'desc': 'Reset the game world map only.' },
    { 'key': 'wipe-world-all', 'name': 'Reset All', 'icon': 'fa-explosion',
      'desc': 'Reset game world map and configuration.' }];

  const consoleCommands = {
    'console': {
      'send': [
        {name: 'help', input: 'display'},
        {name: 'line', input: 'text>', type: 'string', label: null}
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
        <div class="content">
          <p>For help with configuration, see the
          <ExtLink
             href="https://docs.smartlydressedgames.com/en/stable/servers/server-hosting.html#how-to-configure-server"
             wrap>server guide</ExtLink>
          on the docs website.<br />
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
