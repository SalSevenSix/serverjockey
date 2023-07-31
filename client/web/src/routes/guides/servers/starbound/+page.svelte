<script>
  import { scrollto } from 'svelte-scrollto-element';
  import BackToTop from '$lib/BackToTop.svelte';
  import WebappServerInstall from '../WebappServerInstall.svelte';
  import WebappConfigRun from '../WebappConfigRun.svelte';
  import WebappGenerateConfig from '../WebappGenerateConfig.svelte';
</script>


<div class="columns">
  <div class="column is-one-quarter">
    <figure class="image pt-3"><img src="/assets/icons/sb_icon.jpg" alt="Starbound icon" /></figure>
  </div>
  <div class="column is-three-quarters content">
    <h2 class="title is-3 mt-2">Starbound</h2>
    <p>
      <a href="https://playstarbound.com" target="_blank">Starbound <i class="fa fa-up-right-from-square"></i></a>
      is an action-adventure game with fighting, mining and crafting in a procedurally generated 2D world.
      It has RPG elements and a focus on exploration and player guided storytelling.
    </p>
    <p>
      This guide will show you how to install, configure and run a Starbound server using this Webapp.
    </p>
    <p>
      Go to the <a href="#additionalInformation" use:scrollto={'#additionalInformation'}>additional information</a>
      section at the end for help on;
    </p>
    <ul>
      <li><a href="#portForwarding" use:scrollto={'#portForwarding'}>Port Forwarding</a></li>
      <li><a href="#mods" use:scrollto={'#mods'}>Mods</a></li>
    </ul>
  </div>
</div>

<WebappServerInstall module="starbound" />
<WebappGenerateConfig />
<WebappConfigRun />

<div class="content" id="additionalInformation">
  <hr />
  <h3 class="title is-4">Additional Information</h3>
</div>

<div class="content" id="portForwarding">
  <h4 class="title is-5">Port Forwarding</h4>
  <p>
    In order for people to connect to your Starbound server over the internet, your home
    router (internet gateway / &quot;modem&quot;) needs to be configured to forward ports to the server.
    <span class="is-italic">By default ServerJockey will automatically forward ports using UPnP.</span>
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
      <tr><td>Server</td><td>21025</td><td>TCP</td></tr>
    </tbody>
  </table>
  <p>
    If using manual port forwarding you should also disable UPnP in the
    <span class="has-text-weight-bold">Launch Options</span>.
  </p>
  <pre class="pre is-thinner"
>&quot;_comment_server_upnp&quot;: &quot;Try to automatically redirect server ports on home network using UPnP&quot;,
&quot;server_upnp&quot;: false,
&quot;_comment_rcon_upnp&quot;: &quot;Try to automatically redirect rcon port on home network using UPnP&quot;,
&quot;rcon_upnp&quot;: false</pre>
</div>

<div class="content" id="mods">
  <h4 class="title is-5">Mods</h4>
  <p>
    Starbound servers require a Steam account with game licence to download and install.
    Because of this, subscribed Workshop mods are also downloaded.
    ServerJockey will automatically use these mods on the server when it is started.
  </p>
  <p>
    Any changes to subscribed or unsubscribed mods on the Steam account will require a runtime update to take effect.
    Go to the <span class="has-text-weight-bold">Deployment</span> section for the instance, then use
    <span class="has-text-weight-bold">Install Runtime</span> to update the server with mod changes.
  </p>
</div>

<BackToTop />
