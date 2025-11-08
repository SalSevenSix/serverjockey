<script>
  import { surl } from '$lib/util/sjgmsapi';
  import { worldActions, consoleCommands } from './projectzomboid.js';
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
  import CommandBuilder from '$lib/instance/CommandBuilder.svelte';
  import StoreInstance from '$lib/instance/StoreInstance.svelte';
  import Autobackups from './Autobackups.svelte';
</script>


<ServerStatusStore>
  <InstanceHeader />
  <div class="columns">
    <div class="column">
      <div class="columns">
        <div class="column">
          <ServerControls canRestartAfterWarnings canRestartOnEmpty />
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
        <Players hasSteamId />
      </Collapsible>
      <Collapsible icon="fa-file-code" title="Configuration">
        <div class="content">
          <p>
            For help understanding Project Zomboid configuration files. See the
            <ExtLink href="https://steamcommunity.com/sharedfiles/filedetails/?id=2682570605"
                     wrap>excellent guide on Steam</ExtLink>
            by Aiteron. Also, consider using
            <a href={surl('/guides/extension')}>the Browser Extension</a>
            for mod configuration.
            <br />Default configuration files are not generated until after first server start.
          </p>
        </div>
        <ConfigFile name="INI Settings" path="/config/ini" />
        <ConfigFile name="Sandbox Settings" path="/config/sandbox" />
        <ConfigFile name="Spawn Regions" path="/config/spawnregions" />
        <ConfigFile name="Spawn Points" path="/config/spawnpoints" />
        <ConfigFile name="Launch Options" path="/config/cmdargs" />
        <ConfigFile name="JVM Settings" path="/config/jvm">
          <p>
            Change -Xmx to set the memory available to the server.
            e.g. &quot;-Xmx8g&quot; for 8Gb memory.
          </p>
        </ConfigFile>
      </Collapsible>
      <Collapsible icon="fa-scroll" title="Logging">
        <LogFiles allowDelete={1} />
      </Collapsible>
      <Collapsible icon="fa-gears" title="Deployment">
        <RuntimeControls />
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
