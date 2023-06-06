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
    To do this, login to your router then forward ports as shown below. Use of the public IP address as shown
    on the ServerJockey console. More detailed instructions cannot be provided because each router will have
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

<div class="content" id="memoryAllocation">
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

<BackToTop />
