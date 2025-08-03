<script>
  import { scrollto } from 'svelte-scrollto-next';
  import ExtLink from '$lib/widget/ExtLink.svelte';
  import WebappTitle from '../WebappTitle.svelte';
  import WebappServerInstall from '../WebappServerInstall.svelte';
  import WebappConfigRun from '../WebappConfigRun.svelte';
  import WebappAdditionalInformation from '../WebappAdditionalInformation.svelte';
  import WebappPortForward from '../WebappPortForward.svelte';
</script>


<WebappTitle module="csii" serverName="Counter Strike 2">
  <p>
    <ExtLink href="https://www.counter-strike.net" notranslate>Counter Strike 2</ExtLink>
    is a popular competitive PvP FPS built on the Source 2 engine.
    This guide will show you how to install, configure and run
    a Counter Strike 2 server using this Webapp.
  </p>
  <p>
    Jump to the <a href="#portForwarding" use:scrollto={'#portForwarding'}>Port Forwarding</a>
    section at the end for information on ports.
  </p>
</WebappTitle>
<WebappServerInstall module="csii" />
<WebappConfigRun />
<WebappAdditionalInformation />
<WebappPortForward serverName="Counter Strike 2" configName="Command Line Args"
                   portsList={[{ purpose: 'Server', port: 27015, protocal: 'TCP and UDP' }]}>
&quot;_comment_upnp&quot;: &quot;Try to automatically redirect server port on home network using UPnP&quot;,
&quot;upnp&quot;: false
</WebappPortForward>
