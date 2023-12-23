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
  import Iframe from '$lib/Iframe.svelte';
  import ConfigFile from '$lib/ConfigFile.svelte';
  import InstallRuntime from '$lib/InstallRuntime.svelte';
  import DeploymentActions from '$lib/DeploymentActions.svelte';
  import BackupRestoreActions from '$lib/BackupRestoreActions.svelte';
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
         <Iframe />
      </Collapsible>
      <Collapsible icon="fa-user" title="Players">
        <Players />
      </Collapsible>
      <Collapsible icon="fa-file-code" title="Configuration">
        <div class="content">
          <p>
            For help with configuration, see the
            <a href="https://developer.valvesoftware.com/wiki/7_Days_to_Die_Dedicated_Server#Serverconfig.xml"
               target="_blank">dedicated server guide <i class="fa fa-up-right-from-square"></i></a>
            on the wiki.<br /> Default Admin config file is not generated until after first server start.
          </p>
        </div>
        <ConfigFile name="Launch Options" path="/config/cmdargs" />
        <ConfigFile name="Settings" path="/config/settings">
          <p>Note that &quot;Folder and file locations&quot; settings will be ignored.</p>
        </ConfigFile>
        <ConfigFile name="Admin" path="/config/admin" />
      </Collapsible>
      <Collapsible icon="fa-scroll" title="Logging">
        <LogFiles allowDelete={1} />
      </Collapsible>
      <Collapsible icon="fa-gears" title="Deployment">
        <InstallRuntime qualifierName="Beta" />
        <DeploymentActions actions={deploymentActions} />
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
