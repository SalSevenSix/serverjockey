<script>
  import { worldActions } from './hytale.js';
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
  import Autobackups from '$lib/instance/Autobackups.svelte';
  import WorldConfig from './WorldConfig.svelte';
  import Modfiles from './Modfiles.svelte';
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
          <ServerStatus noSteamUrl />
        </div>
      </div>
      <InstanceLog />
      <Collapsible icon="fa-keyboard" title="Console Commands">
        <CommandBuilder />
      </Collapsible>
      <Collapsible icon="fa-user" title="Players">
        <Players />
      </Collapsible>
      <Collapsible icon="fa-file-code" title="Server Config">
        <ConfigFile name="Command Line Args" path="/config/cmdargs">
          <p>See &quot;_comment_...&quot; fields for description of configuration fields.</p>
        </ConfigFile>
        <ConfigFile name="Settings" path="/config/settings" />
        <ConfigFile name="Permissions" path="/config/permissions" />
        <ConfigFile name="Whitelist" path="/config/whitelist" />
        <ConfigFile name="Bans" path="/config/bans" />
        <ConfigFile name="Memories" path="/config/memories" />
        <ConfigFile name="Warps" path="/config/warps" />
      </Collapsible>
      <Collapsible icon="fa-file-fragment" title="Universe Config">
        <WorldConfig />
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
             Authorise device for install when prompted. Delete Runtime first for full re-install.</p>
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
