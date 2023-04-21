<script>
  import Instance from '$lib/Instance.svelte';
  import Collapsible from '$lib/Collapsible.svelte';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
  import Players from '$lib/Players.svelte';
  import ConsoleLog from '$lib/ConsoleLog.svelte';
  import FileSystem from '$lib/FileSystem.svelte';
  import Iframe from '$lib/Iframe.svelte';
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
      <ConsoleLog />
      <Collapsible title="Logging">
        <FileSystem allowDelete />
      </Collapsible>
      <Collapsible title="Console Commands">
         <Iframe />
      </Collapsible>
      <Collapsible title="Configuration">
        <div class="content">
          <p>For help with configuration, see the
             <a href="https://developer.valvesoftware.com/wiki/7_Days_to_Die_Dedicated_Server#Serverconfig.xml"
                target="_blank">dedicated server guide</a> on the wiki.</p>
        </div>
        <ConfigFile name="Settings" path="/config/settings">
          <p>Note that &quot;Folder and file locations&quot; settings will be ignored.</p>
        </ConfigFile>
        <ConfigFile name="Admin" path="/config/admin" />
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
