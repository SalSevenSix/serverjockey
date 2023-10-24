<script>
  import { scrollto } from 'svelte-scrollto-element';
  import BackToTop from '$lib/BackToTop.svelte';
  import WebappServerInstall from '../WebappServerInstall.svelte';
  import WebappConfigRun from '../WebappConfigRun.svelte';
  import WebappPortForward from '../WebappPortForward.svelte';
</script>


<div class="columns">
  <div class="column is-one-quarter">
    <figure class="image pt-3"><img src="/assets/icons/csii_icon.jpg" alt="Counter Strike 2 icon" /></figure>
  </div>
  <div class="column is-three-quarters content">
    <h2 class="title is-3 mt-2">Counter Strike 2</h2>
    <p>
      <a href="https://www.counter-strike.net" target="_blank">Counter Strike 2
      <i class="fa fa-up-right-from-square"></i></a> is a popular competitive PvP FPS built on the Source 2 engine.
      This guide will show you how to install, configure and run a Counter Strike 2 server using this Webapp.
    </p>
    <p>
      Jump to the <a href="#portForwarding" use:scrollto={'#portForwarding'}>Port Forwarding</a>
      section at the end for information on ports.
    </p>
  </div>
</div>

<WebappServerInstall module="csii" />
<WebappConfigRun />

<div class="content" id="additionalInformation">
  <hr />
  <h3 class="title is-4">Additional Information</h3>
</div>

<WebappPortForward serverName="Counter Strike 2" configName="Command Line Args"
                   portsList={[{ purpose: 'Server', port: 27015, protocal: 'TCP and UDP' }]}>
&quot;_comment_upnp&quot;: &quot;Try to automatically redirect server port on home network using UPnP&quot;,
&quot;upnp&quot;: false
</WebappPortForward>

<BackToTop />
