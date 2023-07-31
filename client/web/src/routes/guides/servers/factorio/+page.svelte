<script>
  import { scrollto } from 'svelte-scrollto-element';
  import BackToTop from '$lib/BackToTop.svelte';
  import WebappServerInstall from '../WebappServerInstall.svelte';
  import WebappConfigRun from '../WebappConfigRun.svelte';
</script>


<div class="columns">
  <div class="column is-one-quarter">
    <figure class="image pt-3"><img src="/assets/icons/ft_icon.jpg" alt="Factorio icon" /></figure>
  </div>
  <div class="column is-three-quarters content">
    <h2 class="title is-3 mt-2">Factorio</h2>
    <p>
      <a href="https://www.factorio.com" target="_blank">Factorio <i class="fa fa-up-right-from-square"></i></a>
      is a game where you build, maintain and protect a factory. This involves mining resources,
      researching technologies, building infrastructure, automating production, and fighting enemies.
    </p>
    <p>
      This guide will show you how to install, configure and run a Factorio server using this Webapp.
    </p>
    <p>
      Jump to the <a href="#portForwarding" use:scrollto={'#portForwarding'}>Port Forwarding</a>
      section at the end for information on ports.
    </p>
  </div>
</div>

<WebappServerInstall module="factorio" />
<WebappConfigRun />

<div class="content" id="additionalInformation">
  <hr />
  <h3 class="title is-4">Additional Information</h3>
</div>

<div class="content" id="portForwarding">
  <h4 class="title is-5">Port Forwarding</h4>
  <p>
    In order for people to connect to your Factorio server over the internet, your home
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
      <tr><td>Server</td><td>34197</td><td>UDP</td></tr>
    </tbody>
  </table>
  <p>
    If using manual port forwarding you should also disable UPnP in the
    <span class="has-text-weight-bold">Command Line Args</span> configuration.
  </p>
  <pre class="pre is-thinner"
>&quot;_comment_server-upnp&quot;: &quot;Try to automatically redirect server port on home network using UPnP.&quot;,
&quot;server-upnp&quot;: false,
&quot;_comment_rcon-upnp&quot;: &quot;Try to automatically redirect rcon port on home network using UPnP.&quot;,
&quot;rcon-upnp&quot;: false</pre>
</div>

<BackToTop />
