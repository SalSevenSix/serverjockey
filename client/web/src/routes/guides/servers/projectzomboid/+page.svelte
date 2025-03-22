<script>
  import { scrollto } from 'svelte-scrollto-next';
  import ExtLink from '$lib/widget/ExtLink.svelte';
  import BackToTop from '$lib/widget/BackToTop.svelte';
  import CodeBlock from '$lib/widget/CodeBlock.svelte';
  import WebappTitle from '../WebappTitle.svelte';
  import WebappServerInstall from '../WebappServerInstall.svelte';
  import WebappConfigRun from '../WebappConfigRun.svelte';
  import WebappGenerateConfig from '../WebappGenerateConfig.svelte';
  import WebappAdditionalInformation from '../WebappAdditionalInformation.svelte';
  import WebappPortForward from '../WebappPortForward.svelte';
</script>


<WebappTitle module="projectzomboid" serverName="Project Zomboid">
  <p>
    <ExtLink href="https://projectzomboid.com" notranslate>Project Zomboid</ExtLink>
    is a zombie apocalypse survival horror game set in an open world using an isometric view with 3D elements.
    Gameplay involves combat, exploration, crafting, base building and RPG elements with a focus on realism.
  </p>
  <p>
    This guide will show you how to install, configure and run a Project Zomboid server using this Webapp.
  </p>
  <p>
    Go to the <a href="#additionalInformation" use:scrollto={'#additionalInformation'}>additional information</a>
    section at the end for help on;
  </p>
  <ul>
    <li><a href="#portForwarding" use:scrollto={'#portForwarding'}>Port Forwarding</a></li>
    <li><a href="#memoryAllocation" use:scrollto={'#memoryAllocation'}>Memory Allocation</a></li>
    <li><a href="#adminCharacter" use:scrollto={'#adminCharacter'}>Admin Character</a></li>
    <li><a href="#modUpdateRestarts" use:scrollto={'#modUpdateRestarts'}>Restarts for Mod updates</a></li>
    <li><a href="#integrationMods" use:scrollto={'#integrationMods'}>Integration Mods</a></li>
    <li><a href="#cacheLockingMapFiles" use:scrollto={'#cacheLockingMapFiles'}>Cache Locking Map Files</a></li>
    <li><a href="#dockerPtero" use:scrollto={'#dockerPtero'}>Docker/Pterodactyl Issue</a></li>
  </ul>
</WebappTitle>
<WebappServerInstall module="projectzomboid" />
<WebappGenerateConfig />
<WebappConfigRun />
<WebappAdditionalInformation />
<WebappPortForward serverName="Project Zomboid" configName="INI Settings" upnpService="the server"
  portsList={[{ purpose: 'Steam', port: 16261, protocal: 'UDP' }, { purpose: 'Direct', port: 16262, protocal: 'UDP' }]}>
# Attempt to configure a UPnP-enabled internet gateway to automatically setup port forwarding rules.
# The server will fall back to default ports if this fails.
UPnP=false
</WebappPortForward>

<div class="content pt-4" id="memoryAllocation">
  <h4 class="title is-5">Memory Allocation</h4>
  <p>
    The Project Zomboid server has a memory allocation.
    This is defined in the <span class="has-text-weight-bold">JVM Settings</span>.
    Find the <span class="has-text-weight-bold">-Xmx</span>
    argument under <span class="has-text-weight-bold">vmArgs</span> section.
    By default 8g (8Gb) is allocated. You can adjust as needed.
    As a general rule, the memory required is 2Gb + 500Mb per player. Whatever value is set,
    the machine that the server is running on should have 2Gb more of free memory.
  </p>
  <CodeBlock nocopy>
"vmArgs": [
    "-Djava.awt.headless=true",
    "-Xmx8g",
    "-Dzomboid.steam=1",
    "-Dzomboid.znetlog=1",
    "-Djava.library.path=linux64/:natives/",
    "-Djava.security.egd=file:/dev/urandom",
    "-XX:+UseZGC",
    "-XX:-OmitStackTraceInFastThrow"
]</CodeBlock>
</div>

<div class="content pt-4" id="adminCharacter">
  <h4 class="title is-5">Admin Character</h4>
  <p>
    When a Project Zomboid server starts it will generate a new map if one does not exist.
    It will also create an Admin user called
    <span class="is-family-monospace notranslate">admin</span>.
    You can login to the game world with this user to play as the admin character.
    The password is the same as the Webapp login token. It will not change when the token changes.
  </p>
  <p>
    Note that in the <span class="has-text-weight-bold">Console Commands</span>
    section you can make any user an admin by using Set Access Level to admin.
  </p>
</div>

<div class="content pt-4" id="modUpdateRestarts">
  <h4 class="title is-5">Restarts for Mod updates</h4>
  <p>
    ServerJockey will automatically restart a Project Zomboid server if any of the mods used have been updated on
    the Steam Workshop. By default, the mods are checked every 20 minutes. This interval can be changed in the
    <span class="has-text-weight-bold">Launch Options</span>
    configuration. Use 0 minutes to disable automatic restarts.
  </p>
  <p>
    By default, a warning to players is given 5 minutes and 1 minute before the restart.
    Other action options are available in the configuration. These are explained in the configuration comments.
  </p>
  <CodeBlock nocopy>
&quot;_comment_mod_check_minutes&quot;: &quot;Check interval for updated mods in minutes. Use 0 to disable checks.&quot;,
&quot;mod_check_minutes&quot;: 20,
&quot;_comment_mod_check_action&quot;: &quot;Action to take after updated mods have been detected. Options: 1=NotifyOnly 2=RestartOnEmpty 3=RestartAfterWarnings 4=RestartImmediately&quot;,
&quot;mod_check_action&quot;: 3,</CodeBlock>
</div>

<div class="content pt-4" id="integrationMods">
  <h4 class="title is-5">Integration Mods</h4>
  <p>
    Project Zomboid mods are available to integrate with ServerJockey.
    They provide additional features. Using these mods are optional.
  </p>
  <div class="integration-mods-container"><table class="table is-thinner">
    <thead>
      <tr>
        <th>Workshop ID</th>
        <th>Mod ID</th>
        <th>Description</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td class="white-space-nowrap notranslate">
          <ExtLink href="https://steamcommunity.com/sharedfiles/filedetails/?id=2740018049">2740018049</ExtLink>
        <td class="notranslate">PITaPD</td>
        <td>Adds the in-game date &amp; time to the server status in both the webapp and discord.
            Also player death event messages are sent to discord.</td>
      </tr>
    </tbody>
  </table></div>
</div>

<div class="content pt-4" id="cacheLockingMapFiles">
  <h4 class="title is-5">Cache Locking Map Files</h4>
  <p>
    ServerJockey has a feature to boost performance on high player count servers.
    The game map is stored in many small files which can cause disk IO to be a bottleneck.
    The Cache Lock feature will pre-cache all map files in memory, same as the OS would normally
    do when files are read. However this feature will also lock them in, preventing eviction until
    the server has stopped. Therefore all map files will be read from memory, with writes still
    done to disk.
  </p>
  <p>
    For this feature to work, you need
    <span class="is-family-monospace notranslate">vmtouch</span>
    installed on the machine.
    <span class="is-italic">The VirtualBox and Docker/Pterodactyl distributions
    of ServerJockey already have this pre-installed.</span>
    For the DEB, RPM and Source distributions, use the appropriate package manager to install;
    e.g.
  </p>
  <CodeBlock>sudo apt install vmtouch</CodeBlock>
  <p>
    The OS has a limit on how much memory can be locked. This has been raised to
    <span class="has-text-weight-bold">8Gb</span> in the DEB, RPM and VirtualBox distributions.
    For these distributions the higher limit is set in the systemd service file;
  </p>
  <CodeBlock>/etc/systemd/system/serverjockey.service</CodeBlock>
  <p>
    For the Docker distribution, a higher limit can be set when the image is first run;
  </p>
  <CodeBlock>docker run --ulimit memlock=8589934592:8589934592 -p 6164:6164/tcp &lt;image&gt;:&lt;tag&gt;</CodeBlock>
  <p>
    For the Pterodactyl distribution It&#39;s not possible to add arguments when the docker image is run.
    You can raise the global limit for systemd which will apply to all docker containers.
  </p>
  <CodeBlock>/etc/systemd/system.conf</CodeBlock>
  <CodeBlock>DefaultLimitMEMLOCK=8589934592:8589934592</CodeBlock>
  <p>
    For the Source distribution, you must raise the limit yourself by editing the limits configuration;
  </p>
  <CodeBlock>/etc/security/limits.conf</CodeBlock>
  <p>
    Finally, with
    <span class="is-family-monospace notranslate">vmtouch</span>
    installed, this feature can be enabled in the
    <span class="has-text-weight-bold">Launch Options</span>
    configuration. Please ensure enough free memory is available when cache locking the map files.
  </p>
  <CodeBlock nocopy>
&quot;_comment_cache_map_files&quot;: &quot;Force map files to be cached in memory while server is running&quot;,
&quot;cache_map_files&quot;: true</CodeBlock>
</div>

<div class="content pt-4" id="dockerPtero">
  <h4 class="title is-5">Docker/Pterodactyl Issue</h4>
  <p>
    There is
    <ExtLink href="https://theindiestone.com/forums/index.php?/topic/49783-javautilconcurrentexecutionexception-javaioioexception-no-space-left-on-device"
             wrap>a known issue</ExtLink>
    running the Project Zomboid dedicated server on Docker as well as Pterodactyl because it uses Docker.
    The server will often crash while starting around the automatic map backup stage.
    The workaround is simply to disable all of the automatic map backups in the
    <span class="has-text-weight-bold">INI Settings</span>.
  </p>
  <CodeBlock nocopy>
BackupsOnStart=false
BackupsOnVersionChange=false</CodeBlock>
  <p>
    Also delete any map backups that the server made.
    Use the <span class="has-text-weight-bold">Autobackups</span> section in the webapp to do this.
    Then restart the Docker container.
  </p>
</div>

<BackToTop />


<style>
  .integration-mods-container {
    overflow-x: auto;
  }

  .integration-mods-container .table {
    min-width: 26em;
  }
</style>
