<script>
  import ServerStatusStore from '$lib/ServerStatusStore.svelte';
  import Instance from '$lib/Instance.svelte';
  import Collapsible from '$lib/Collapsible.svelte';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerConfig from '$lib/ServerConfig.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
  import Players from '$lib/Players.svelte';
  import InstanceLog from '$lib/InstanceLog.svelte';
  import ConfigFile from '$lib/ConfigFile.svelte';
  import LogFiles from '$lib/LogFiles.svelte';
  import CommandBuilder from '$lib/CommandBuilder.svelte';
  import InstallRuntime from '$lib/InstallRuntime.svelte';
  import BackupRestoreActions from '$lib/BackupRestoreActions.svelte';
  import CheckStore from '$lib/CheckStore.svelte';
  import ContextInstanceWrapper from '$lib/ContextInstanceWrapper.svelte';
  import InstanceActivity from '$lib/InstanceActivity.svelte';

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
        <ConfigFile name="Command Line Args" path="/config/cmdargs" />
      </Collapsible>
      <Collapsible icon="fa-scroll" title="Logging">
        <LogFiles allowDelete={1} />
      </Collapsible>
      <Collapsible icon="fa-gears" title="Deployment">
        <InstallRuntime qualifierName="Beta (optional)" />
      </Collapsible>
      <Collapsible icon="fa-box-archive" title="Backups">
        <BackupRestoreActions hasWorld={false} />
      </Collapsible>
      <CheckStore>
        <Collapsible icon="fa-chart-pie" title="Activity">
          <ContextInstanceWrapper let:instance={instance}>
            <InstanceActivity criteria={{ instance: instance.identity() }} />
          </ContextInstanceWrapper>
        </Collapsible>
      </CheckStore>
    </div>
  </div>
</Instance></ServerStatusStore>
