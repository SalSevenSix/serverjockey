<script>
  import { scrollto } from 'svelte-scrollto-element';
  import BackToTop from '$lib/BackToTop.svelte';
  import WebappTitle from '../WebappTitle.svelte';
  import WebappServerInstall from '../WebappServerInstall.svelte';
  import WebappConfigRun from '../WebappConfigRun.svelte';
  import WebappGenerateConfig from '../WebappGenerateConfig.svelte';
  import WebappPortForward from '../WebappPortForward.svelte';
</script>


<WebappTitle module="starbound" serverName="Starbound">
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
</WebappTitle>

<WebappServerInstall module="starbound" />
<WebappGenerateConfig />
<WebappConfigRun />

<div class="content" id="additionalInformation">
  <hr />
  <h3 class="title is-4">Additional Information</h3>
</div>

<WebappPortForward serverName="Starbound" configName="Launch Options"
                   portsList={[{ purpose: 'Server', port: 21025, protocal: 'TCP' }]}>
&quot;_comment_server_upnp&quot;: &quot;Try to automatically redirect server ports on home network using UPnP&quot;,
&quot;server_upnp&quot;: false,
&quot;_comment_rcon_upnp&quot;: &quot;Try to automatically redirect rcon port on home network using UPnP&quot;,
&quot;rcon_upnp&quot;: false
</WebappPortForward>

<div class="content pt-4" id="mods">
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
