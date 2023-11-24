<script>
  import ServerStatusStore from '$lib/ServerStatusStore.svelte';
  import InstanceHeader from '$lib/InstanceHeader.svelte';
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
  import Autosaves from './Autosaves.svelte';
  import CheckStore from '$lib/CheckStore.svelte';
  import InstanceActivity from '$lib/InstanceActivity.svelte';
  import PlayerActivity from '$lib/PlayerActivity.svelte';
  import ChatActivityGadget from '$lib/ChatActivityGadget.svelte';

  const deploymentActions = [
    { 'key': 'wipe-world-save', 'name': 'Reset Save',
      'desc': 'Reset the game world save only.' },
    { 'key': 'wipe-world-config', 'name': 'Reset Config',
      'desc': 'Reset the configuration files only.' },
    { 'key': 'wipe-world-all', 'name': 'Reset All', 'icon': 'fa-explosion',
      'desc': 'Reset all of the above.' }];

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
      <InstanceLog canDownload />
      <Collapsible icon="fa-keyboard" title="Console Commands">
        <CommandBuilder commands={consoleCommands} />
      </Collapsible>
      <Collapsible icon="fa-user" title="Players">
        <Players />
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
            For automatic mod downloading both username and token in the
            <span class="has-text-weight-bold">Server</span> configuration need to be set.
            You can find these credentials in your Factorio profile i.e.
            <span class="is-family-monospace is-size-6">
              C:\Users\&lt;YOU&gt;\AppData\Roaming\Factorio\player-data.json</span><br />
            Mod version can optionally be specified using
            <span class="is-family-monospace is-size-6">
              &quot;version&quot;: &quot;&lt;version&gt;&quot;</span>
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
        <LogFiles />
      </Collapsible>
      <Collapsible icon="fa-gears" title="Deployment">
        <InstallRuntime qualifierName="Version (optional)" />
        <DeploymentActions actions={deploymentActions} />
      </Collapsible>
      <Collapsible icon="fa-file-zipper" title="Autosaves">
        <Autosaves />
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
          <ChatActivityGadget />
        </Collapsible>
      </CheckStore>
    </div>
  </div>
</ServerStatusStore>
