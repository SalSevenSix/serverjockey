<script>
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
  import Autosaves from './Autosaves.svelte';

  const worldActions = [
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
            <span class="is-family-monospace is-size-6 notranslate">
              C:\Users\&lt;YOU&gt;\AppData\Roaming\Factorio\player-data.json</span><br />
            Mod version can optionally be specified using
            <span class="is-family-monospace is-size-6 notranslate">
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
        <RuntimeControls qualifierName="Version" />
        <WorldControls actions={worldActions} />
      </Collapsible>
      <Collapsible icon="fa-file-zipper" title="Autosaves">
        <Autosaves />
      </Collapsible>
      <Collapsible icon="fa-box-archive" title="Backups">
        <BackupRestoreActions />
      </Collapsible>
      <StoreInstance />
    </div>
  </div>
</ServerStatusStore>
