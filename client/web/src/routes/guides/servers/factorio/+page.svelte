<script>
  import { scrollto } from 'svelte-scrollto-next';
  import ExtLink from '$lib/widget/ExtLink.svelte';
  import BackToTop from '$lib/widget/BackToTop.svelte';
  import WebappTitle from '../WebappTitle.svelte';
  import WebappServerInstall from '../WebappServerInstall.svelte';
  import WebappConfigRun from '../WebappConfigRun.svelte';
  import WebappAdditionalInformation from '../WebappAdditionalInformation.svelte';
  import WebappPortForward from '../WebappPortForward.svelte';
</script>


<WebappTitle module="factorio" serverName="Factorio">
  <p>
    <ExtLink href="https://www.factorio.com" notranslate>Factorio</ExtLink>
    is a game where you build, maintain and protect a factory. This involves mining resources,
    researching technologies, building infrastructure, automating production, and fighting enemies.
  </p>
  <p>
    This guide will show you how to install, configure and run a Factorio server using this Webapp.
    Both base game and Space Age expansion are supported.
  </p>
  <p>
    Jump to the <a href="#portForwarding" use:scrollto={'#portForwarding'}>Port Forwarding</a>
    section at the end for information on ports.
  </p>
</WebappTitle>
<WebappServerInstall module="factorio" />
<WebappConfigRun />
<WebappAdditionalInformation />
<WebappPortForward serverName="Factorio" configName="Command Line Args"
                   portsList={[{ purpose: 'Server', port: 34197, protocal: 'UDP' }]}>
&quot;_comment_server-upnp&quot;: &quot;Try to automatically redirect server port on home network using UPnP.&quot;,
&quot;server-upnp&quot;: false,
&quot;_comment_rcon-upnp&quot;: &quot;Try to automatically redirect rcon port on home network using UPnP.&quot;,
&quot;rcon-upnp&quot;: false
</WebappPortForward>

<BackToTop />
