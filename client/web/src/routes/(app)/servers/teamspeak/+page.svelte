<script>
  import ExtLink from '$lib/widget/ExtLink.svelte';
  import Collapsible from '$lib/widget/Collapsible.svelte';
  import ServerStatusStore from '$lib/instance/ServerStatusStore.svelte';
  import InstanceHeader from '$lib/instance/InstanceHeader.svelte';
  import ServerStatus from '$lib/instance/ServerStatus.svelte';
  import ServerConfig from '$lib/instance/ServerConfig.svelte';
  import ServerControls from '$lib/instance/ServerControls.svelte';
  import InstanceLog from '$lib/instance/InstanceLog.svelte';
  import LogFiles from '$lib/instance/LogFiles.svelte';
  import ConfigFile from '$lib/instance/ConfigFile.svelte';
  import RuntimeControls from '$lib/instance/RuntimeControls.svelte';
  import WorldControls from '$lib/instance/WorldControls.svelte';
  import BackupRestoreActions from '$lib/instance/BackupRestoreActions.svelte';

  const worldActions = [
    { 'key': 'wipe-world-config', 'name': 'Reset Config',
      'desc': 'Reset all configuration files.' },
    { 'key': 'wipe-world-logs', 'name': 'Delete Logs',
      'desc': 'Delete the log files only.' },
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
      <Collapsible icon="fa-scroll" title="Logging">
        <LogFiles allowDelete={1} />
      </Collapsible>
      <Collapsible icon="fa-file-code" title="Configuration">
        <div class="content"><p>
          For help on TeamSpeak configuration files, see the
          <ExtLink href="https://tserverhq.com/clients/knowledgebase/132/How-do-I-use-the-ts3serverini-file.html">
            knowledgebase page</ExtLink>
        </p></div>
        <ConfigFile name="INI Settings" path="/config/ini" />
        <ConfigFile name="IP Allowlist" path="/config/allowlist" />
        <ConfigFile name="IP Denylist" path="/config/denylist" />
      </Collapsible>
      <Collapsible icon="fa-gears" title="Deployment">
        <RuntimeControls qualifierName="Version" />
        <WorldControls actions={worldActions} />
      </Collapsible>
      <Collapsible icon="fa-box-archive" title="Backups">
        <BackupRestoreActions />
      </Collapsible>
    </div>
  </div>
</ServerStatusStore>
