<script>
  import Collapsible from '$lib/widget/Collapsible.svelte';
  import ServerStatusStore from '$lib/instance/ServerStatusStore.svelte';
  import InstanceHeader from '$lib/instance/InstanceHeader.svelte';
  import ServerStatus from '$lib/instance/ServerStatus.svelte';
  import ServerConfig from '$lib/instance/ServerConfig.svelte';
  import ServerControls from '$lib/instance/ServerControls.svelte';
  import InstanceLog from '$lib/instance/InstanceLog.svelte';
  import RuntimeControls from '$lib/instance/RuntimeControls.svelte';
  import WorldControls from '$lib/instance/WorldControls.svelte';
  import LogFiles from '$lib/instance/LogFiles.svelte';
  import ConfigFile from '$lib/instance/ConfigFile.svelte';

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
      <Collapsible icon="fa-file-code" title="Configuration">
        <div class="content">
          <p>
            Default list files are not generated until after first server start.
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
    </div>
  </div>
</ServerStatusStore>
