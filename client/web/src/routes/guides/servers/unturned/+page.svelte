<script>
  import { scrollto } from 'svelte-scrollto-next';
  import ExtLink from '$lib/widget/ExtLink.svelte';
  import BackToTop from '$lib/widget/BackToTop.svelte';
  import WebappTitle from '../WebappTitle.svelte';
  import WebappServerInstall from '../WebappServerInstall.svelte';
  import WebappConfigRun from '../WebappConfigRun.svelte';
  import WebappGenerateConfig from '../WebappGenerateConfig.svelte';
  import WebappAdditionalInformation from '../WebappAdditionalInformation.svelte';
  import WebappPortForward from '../WebappPortForward.svelte';
</script>


<WebappTitle module="unturned" serverName="Unturned">
  <p>
    <ExtLink href="https://smartlydressedgames.com" notranslate>Unturned</ExtLink>
    is a free-to-play zombie apocalypse survival game set in a 3D open world.
    It features combat, looting, gear upgrades, exploration, and RPG elements.
  </p>
  <p>
    This guide will show you how to install, configure and run an Unturned server using this Webapp.
  </p>
  <p>
    Jump to the <a href="#portForwarding" use:scrollto={'#portForwarding'}>Port Forwarding</a>
    section at the end for information on ports.
  </p>
</WebappTitle>
<WebappServerInstall module="unturned" />
<WebappGenerateConfig />
<WebappConfigRun />
<WebappAdditionalInformation />
<WebappPortForward serverName="Starbound" configName="Launch Options"
  portsList={[{ purpose: 'Queries', port: 27015, protocal: 'UDP' }, { purpose: 'Server', port: 27016, protocal: 'UDP' }]}>
&quot;_comment_upnp&quot;: &quot;Try to automatically redirect ports on home network using UPnP&quot;,
&quot;upnp&quot;: false
</WebappPortForward>

<BackToTop />
