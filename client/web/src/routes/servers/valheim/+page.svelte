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
  import StoreInstance from '$lib/instance/StoreInstance.svelte';

  const worldActions = [
    { 'key': 'wipe-world-save', 'name': 'Reset Save',
      'desc': 'Reset the game world map only.' },
    { 'key': 'wipe-world-all', 'name': 'Reset All', 'icon': 'fa-explosion',
      'desc': 'Reset game world map and configuration.' }];
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
      <Collapsible icon="fa-user" title="Players">
        <Players />
      </Collapsible>
      <Collapsible icon="fa-file-code" title="Configuration">
        <div class="content">
          <p>
            Help on the lists can be found in the
            <ExtLink href="https://valheim.fandom.com/wiki/Dedicated_servers#Admins,_bans,_and_whitelist">
            Admins, Bans and Whitelist section</ExtLink>
            on the Valheim wiki.
          </p>
        </div>
        <ConfigFile name="Launch Options" path="/config/cmdargs" />
        <ConfigFile name="Admin List" path="/config/adminlist" />
        <ConfigFile name="Permitted List" path="/config/permittedlist" />
        <ConfigFile name="Banned List" path="/config/bannedlist" />
      </Collapsible>
      <Collapsible icon="fa-scroll" title="Logging">
        <LogFiles allowDelete={1} />
      </Collapsible>
      <Collapsible icon="fa-gears" title="Deployment">
        <RuntimeControls qualifierDefault="public" />
        <WorldControls actions={worldActions} />
      </Collapsible>
      <Collapsible icon="fa-box-archive" title="Backups">
        <BackupRestoreActions />
      </Collapsible>
      <StoreInstance />
    </div>
  </div>
</ServerStatusStore>
