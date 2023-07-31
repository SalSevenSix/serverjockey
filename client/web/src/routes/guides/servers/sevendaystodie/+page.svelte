<script>
  import { scrollto } from 'svelte-scrollto-element';
  import BackToTop from '$lib/BackToTop.svelte';
  import WebappServerInstall from '../WebappServerInstall.svelte';
  import WebappConfigRun from '../WebappConfigRun.svelte';
</script>


<div class="columns">
  <div class="column is-one-quarter">
    <figure class="image pt-3"><img src="/assets/icons/7d2d_icon.png" alt="7d2d icon" /></figure>
  </div>
  <div class="column is-three-quarters content">
    <h2 class="title is-3 mt-2">7 Days to Die</h2>
    <p>
      <a href="https://7daystodie.com" target="_blank">7 Days to Die <i class="fa fa-up-right-from-square"></i></a>
      is zombie apocalypse survival horror game set in a 3D open world. It features combat, looting, mining, crafting,
      base building &amp; defence, exploration, and RPG elements.
    </p>
    <p>
      This guide will show you how to install, configure and run a 7 Days to Die server using this Webapp.
    </p>
    <p>
      Jump to the <a href="#portForwarding" use:scrollto={'#portForwarding'}>Port Forwarding</a>
      section at the end for information on ports.
    </p>
  </div>
</div>

<WebappServerInstall module="sevendaystodie" />
<WebappConfigRun />

<div class="content" id="additionalInformation">
  <hr />
  <h3 class="title is-4">Additional Information</h3>
</div>

<div class="content" id="portForwarding">
  <h4 class="title is-5">Port Forwarding</h4>
  <p>
    In order for people to connect to your 7 Days to Die server over the internet, your home
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
      <tr><th>Purpose</th><th>Ports</th><th>Protocal</th></tr>
    </thead>
    <tbody class="is-family-monospace">
      <tr><td>Main</td><td>26900</td><td>TCP and UDP</td></tr>
      <tr><td>Additional</td><td>26901-26903</td><td>UDP</td></tr>
      <tr><td>Webcon (optional)</td><td>8080</td><td>TCP</td></tr>
      <tr><td>Telnet (optional)</td><td>8081</td><td>TCP</td></tr>
    </tbody>
  </table>
  <p>
    If using manual port forwarding you should also disable UPnP in the
    <span class="has-text-weight-bold">Launch Options</span>.
  </p>
  <pre class="pre is-thinner"
>&quot;_comment_server_upnp&quot;: &quot;Try to automatically redirect server ports on home network using UPnP&quot;,
&quot;server_upnp&quot;: false,
&quot;_comment_console_upnp&quot;: &quot;Try to automatically redirect web console port on home network using UPnP&quot;,
&quot;console_upnp&quot;: false,
&quot;_comment_telnet_upnp&quot;: &quot;Try to automatically redirect telnet port on home network using UPnP&quot;,
&quot;telnet_upnp&quot;: false</pre>
</div>

<BackToTop />
