<script>
  import Instance from '$lib/Instance.svelte';
  import Collapsible from '$lib/Collapsible.svelte';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
  import Players from '$lib/Players.svelte';
  import ConsoleLog from '$lib/ConsoleLog.svelte';
  import ConfigFile from '$lib/ConfigFile.svelte';
  import InstallRuntime from '$lib/InstallRuntime.svelte';
  import DeploymentActions from '$lib/DeploymentActions.svelte';
  import BackupRestoreActions from '$lib/BackupRestoreActions.svelte';

  let deploymentActions = {
    'wipe-world-save': 'Reset the game world save only.',
    'wipe-world-config': 'Reset the configuration files only.',
    'wipe-world-all': 'Reset all of the above.'
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
      <Collapsible title="Configuration">
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
            For automatic mod download you need to set both username and token in the
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
      <Collapsible title="Deployment">
        <InstallRuntime qualifierName="Version (optional)" />
        <DeploymentActions actions={deploymentActions} />
      </Collapsible>
      <Collapsible title="Backups">
        <BackupRestoreActions />
      </Collapsible>
    </div>
  </div>
</Instance>
