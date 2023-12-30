<script>
  import ServerStatusStore from '$lib/ServerStatusStore.svelte';
  import InstanceHeader from '$lib/InstanceHeader.svelte';
  import Collapsible from '$lib/Collapsible.svelte';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerConfig from '$lib/ServerConfig.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
  import Players from '$lib/Players.svelte';
  import InstanceLog from '$lib/InstanceLog.svelte';
  import ConfigFile from '$lib/ConfigFile.svelte';
  import LogFiles from '$lib/LogFiles.svelte';
  import CommandBuilder from '$lib/CommandBuilder.svelte';
  import RuntimeControls from '$lib/RuntimeControls.svelte';
  import BackupRestoreActions from '$lib/BackupRestoreActions.svelte';
  import CheckStore from '$lib/CheckStore.svelte';
  import InstanceActivity from '$lib/InstanceActivity.svelte';
  import PlayerActivity from '$lib/PlayerActivity.svelte';
  import ChatActivityGadget from '$lib/ChatActivityGadget.svelte';

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
        <ConfigFile name="Command Line Args" path="/config/cmdargs" />
      </Collapsible>
      <Collapsible icon="fa-scroll" title="Logging">
        <LogFiles allowDelete={1} />
      </Collapsible>
      <Collapsible icon="fa-gears" title="Deployment">
        <RuntimeControls qualifierName="Version" />
      </Collapsible>
      <Collapsible icon="fa-box-archive" title="Backups">
        <BackupRestoreActions hasWorld={false} />
      </Collapsible>
      <CheckStore>
        <Collapsible icon="fa-chart-pie" title="Activity">
          <InstanceActivity />
          <PlayerActivity />
        </Collapsible>
        <Collapsible icon="fa-comments" title="Chat Log">
          <ChatActivityGadget />
        </Collapsible>
      </CheckStore>
    </div>
  </div>
</ServerStatusStore>
