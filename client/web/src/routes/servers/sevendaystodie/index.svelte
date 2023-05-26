<script>
  import Instance from '$lib/Instance.svelte';
  import Collapsible from '$lib/Collapsible.svelte';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerConfig from '$lib/ServerConfig.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
  import Players from '$lib/Players.svelte';
  import ConsoleLog from '$lib/ConsoleLog.svelte';
  import FileSystem from '$lib/FileSystem.svelte';
  import Iframe from '$lib/Iframe.svelte';
  import ConfigFile from '$lib/ConfigFile.svelte';
  import InstallRuntime from '$lib/InstallRuntime.svelte';
  import DeploymentActions from '$lib/DeploymentActions.svelte';
  import BackupRestoreActions from '$lib/BackupRestoreActions.svelte';

  let deploymentActions = [
    { 'key': 'wipe-world-save', 'icon': 'explosion', 'name': 'World Save',
      'desc': 'Reset the game world save only.' },
    { 'key': 'wipe-world-config', 'icon': 'explosion', 'name': 'World Config',
      'desc': 'Reset the configuration files only.' },
    { 'key': 'wipe-world-all', 'icon': 'explosion', 'name': 'World All',
      'desc': 'Reset all of the above.' }];
</script>


<Instance>
  <div class="columns">
    <div class="column">
      <div class="columns">
        <div class="column">
          <ServerControls />
          <ServerConfig />
          <ServerStatus />
        </div>
        <div class="column">
          <Players />
        </div>
      </div>
      <ConsoleLog />
      <Collapsible title="Console Commands">
         <Iframe />
      </Collapsible>
      <Collapsible title="Configuration">
        <div class="content">
          <p>
            For help with configuration, see the
            <a href="https://developer.valvesoftware.com/wiki/7_Days_to_Die_Dedicated_Server#Serverconfig.xml"
               target="_blank">dedicated server guide</a> on the wiki.<br />
            Default Admin config file is not generated until after first server start.
          </p>
        </div>
        <ConfigFile name="Settings" path="/config/settings">
          <p>Note that &quot;Folder and file locations&quot; settings will be ignored.</p>
        </ConfigFile>
        <ConfigFile name="Admin" path="/config/admin" />
      </Collapsible>
      <Collapsible title="Logging">
        <FileSystem allowDelete />
      </Collapsible>
      <Collapsible title="Deployment">
        <InstallRuntime qualifierName="Beta (optional)" />
        <DeploymentActions actions={deploymentActions} />
      </Collapsible>
      <Collapsible title="Backups">
        <BackupRestoreActions />
      </Collapsible>
    </div>
  </div>
</Instance>
