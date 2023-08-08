<script>
  import { scrollto } from 'svelte-scrollto-element';
  import BackToTop from '$lib/BackToTop.svelte';
  import WebappServerInstall from '../WebappServerInstall.svelte';
  import WebappConfigRun from '../WebappConfigRun.svelte';
  import WebappGenerateConfig from '../WebappGenerateConfig.svelte';
</script>


<div class="columns">
  <div class="column is-one-quarter">
    <figure class="image pt-3"><img src="/assets/icons/pz_icon.jpg" alt="Project Zomboid icon" /></figure>
  </div>
  <div class="column is-three-quarters content">
    <h2 class="title is-3 mt-2">Project Zomboid</h2>
    <p>
      <a href="https://projectzomboid.com" target="_blank">
        Project Zomboid <i class="fa fa-up-right-from-square"></i></a>
      is a zombie apocalypse survival horror game set in an open world using an isometric view with 3D elements.
      Gameplay involves combat, crafting, base building and RPG elements with a focus on realism.
      Survival is challenging, requiring the player to continually monitor both the surounding situation
      and the physical and mental state of thier character.
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
      <li><a href="#integrationMods" use:scrollto={'#integrationMods'}>Integration Mods</a></li>
      <li><a href="#cacheLockingMapFiles" use:scrollto={'#cacheLockingMapFiles'}>Cache Locking Map Files</a></li>
      <li><a href="#dockerPtero" use:scrollto={'#dockerPtero'}>Docker/Pterodactyl Issue</a></li>
    </ul>
  </div>
</div>

<WebappServerInstall module="projectzomboid" />
<WebappGenerateConfig />
<WebappConfigRun />

<div class="content" id="additionalInformation">
  <hr />
  <h3 class="title is-4">Additional Information</h3>
</div>

<div class="content" id="portForwarding">
  <h4 class="title is-5">Port Forwarding</h4>
  <p>
    In order for people to connect to your Project Zomboid server over the internet, your home
    router (internet gateway / &quot;modem&quot;) needs to be configured to forward ports to the server.
    <span class="is-italic">By default the server will automatically forward ports using UPnP.</span>
    However, if this is not working on your LAN, you can manually add the port forwarding.
  </p>
  <p>
    To do this, login to your router then forward ports as shown below. Use the local IP address as shown on the
    ServerJockey webapp home page. More detailed instructions cannot be provided because each router will have
    a different webapp interface depending on the brand and model.
  </p>
  <table class="table is-thinner">
    <thead>
      <tr><th>Purpose</th><th>Port</th><th>Protocal</th></tr>
    </thead>
    <tbody class="is-family-monospace">
      <tr><td>Steam</td><td>16261</td><td>UDP</td></tr>
      <tr><td>Direct</td><td>16262</td><td>UDP</td></tr>
    </tbody>
  </table>
  <p>
    If using manual port forwarding you should also disable UPnP in the
    <span class="has-text-weight-bold">INI Settings</span>.
  </p>
  <pre class="pre is-thinner"
># Attempt to configure a UPnP-enabled internet gateway to automatically setup port forwarding rules.
# The server will fall back to default ports if this fails.
UPnP=false</pre>
</div>

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
  <pre class="pre is-thinner">"vmArgs": [
    "-Djava.awt.headless=true",
    "-Xmx8g",
    "-Dzomboid.steam=1",
    "-Dzomboid.znetlog=1",
    "-Djava.library.path=linux64/:natives/",
    "-Djava.security.egd=file:/dev/urandom",
    "-XX:+UseZGC",
    "-XX:-OmitStackTraceInFastThrow"
]</pre>
</div>

<div class="content pt-4" id="integrationMods">
  <h4 class="title is-5">Integration Mods</h4>
  <p>
    Project Zomboid mods are available to integrate with ServerJockey.
    They provide additional features. Using these mods is optional.
  </p>
  <table class="table is-thinner">
    <thead>
      <tr>
        <th>Workshop ID</th>
        <th>Mod ID</th>
        <th>Description</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td class="white-space-nowrap">
          <a href="https://steamcommunity.com/sharedfiles/filedetails/?id=2740018049" target="_blank">
            2740018049 <i class="fa fa-up-right-from-square"></i></a></td>
        <td>PIT</td>
        <td>Adds the in-game date &amp; time to the server status in both the webapp and discord.</td>
      </tr>
      <tr>
        <td class="white-space-nowrap">
          <a href="https://steamcommunity.com/sharedfiles/filedetails/?id=2820127528" target="_blank">
            2820127528 <i class="fa fa-up-right-from-square"></i></a></td>
        <td>ModzCheck</td>
        <td>Enables automatic server restart when a Workshop mod has been updated.
            Players are given restart warning at 5 minutes and 1 minute before restart.</td>
      </tr>
    </tbody>
  </table>
</div>

<div class="content" id="cacheLockingMapFiles">
  <h4 class="title is-5">Cache Locking Map Files</h4>
  <p>
    ServerJockey has an experimental feature to boost performance on high player count servers.
    The game map is stored in many small files which can cause disk IO to be a bottleneck.
    The Cache Lock feature will pre-cache all map files in memory, same as the OS would normally do when
    files are read. However this feature will also lock them in, preventing eviction until the server has stopped.
    Therefore all map files will be read from memory. Writes are still done to disk,
    avoiding risks of ramdisk solutions to this issue.
  </p>
  <p>
    For this feature to work, you need <span class="is-family-monospace">vmtouch</span> installed on the machine.
    The VirtualBox and Docker distributions of ServerJockey already have it pre-installed.
    For the DEB, RPM and Source distributions, use the appropriate package manager to install;
    e.g.
  </p>
  <pre class="pre is-thinner">sudo apt install vmtouch</pre>
  <p>
    With <span class="is-family-monospace">vmtouch</span> installed, this feature can be enabled in the
    <span class="has-text-weight-bold">Launch Options</span> configuration.
    Please ensure enough free memory is available when cache locking the map files.
  </p>
  <pre class="pre is-thinner"
>&quot;_comment_cache_map_files&quot;: &quot;Force map files to be cached in memory while server is running (EXPERIMENTAL)&quot;,
&quot;cache_map_files&quot;: true</pre>
</div>

<div class="content pt-4" id="dockerPtero">
  <h4 class="title is-5">Docker/Pterodactyl Issue</h4>
  <p>
    There is
    <a href="https://theindiestone.com/forums/index.php?/topic/49783-javautilconcurrentexecutionexception-javaioioexception-no-space-left-on-device/" target="_blank">
        a known issue <i class="fa fa-up-right-from-square"></i></a>
    running the Project Zomboid dedicated server on Docker as well as Pterodactyl because it uses Docker.
    The server will often crash while starting around the automatic map backup stage.
    The workaround is simply to disable all of the automatic map backups in the
    <span class="has-text-weight-bold">INI Settings</span>.
  </p>
  <pre class="pre is-thinner">BackupsOnStart=false
BackupsOnVersionChange=false</pre>
  <p>
    Also delete any map backups that the server made.
    Use the <span class="has-text-weight-bold">Autobackups</span> section in the webapp to do this.
    Then restart the Docker container.
  </p>
</div>

<BackToTop />
