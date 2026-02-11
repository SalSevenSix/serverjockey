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
  import Autobackups from '$lib/instance//Autobackups.svelte';
  import Modfiles from './Modfiles.svelte';

  const worldActions = [
    { 'key': 'wipe-world-save', 'name': 'Reset Save',
      'desc': 'Reset the game world save only.' },
    { 'key': 'wipe-world-logs', 'name': 'Delete Logs',
      'desc': 'Delete the log files only.' },
    { 'key': 'wipe-world-autobackups', 'name': 'Delete Autobackups',
      'desc': 'Delete the automatic server created backups.' },
    { 'key': 'wipe-world-all', 'name': 'Reset All', 'icon': 'fa-explosion',
      'desc': 'Reset all of the above.' }];
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
        <CommandBuilder />
      </Collapsible>
      <Collapsible icon="fa-user" title="Players">
        <Players />
      </Collapsible>
      <Collapsible icon="fa-file-code" title="Configuration">
        <ConfigFile name="Command Line Args" path="/config/cmdargs">
          <p>See &quot;_comment_...&quot; fields for description of configuration fields.</p>
        </ConfigFile>
        <ConfigFile name="Server Config" path="/config/config" />
        <ConfigFile name="Permissions" path="/config/permissions" />
        <ConfigFile name="Whitelist" path="/config/whitelist" />
        <ConfigFile name="Bans" path="/config/bans" />
        <ConfigFile name="World Config" path="/config/default" />
      </Collapsible>
      <Collapsible icon="fa-puzzle-piece" title="Mod Files">
        <Modfiles />
      </Collapsible>
      <Collapsible icon="fa-scroll" title="Logging">
        <LogFiles allowDelete={1} />
      </Collapsible>
      <Collapsible icon="fa-gears" title="Deployment">
        <RuntimeControls qualifierName="Patchline">
          <p>Watch server status and console log for authorisation step during install process.
             Authorise device for install when prompted.</p>
        </RuntimeControls>
        <WorldControls actions={worldActions} />
      </Collapsible>
      <Collapsible icon="fa-file-zipper" title="Autobackups">
        <Autobackups />
      </Collapsible>
      <Collapsible icon="fa-box-archive" title="Backups">
        <BackupRestoreActions />
      </Collapsible>
      <StoreInstance />
    </div>
  </div>
</ServerStatusStore>
