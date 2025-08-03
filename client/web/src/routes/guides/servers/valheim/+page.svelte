<script>
  import { scrollto } from 'svelte-scrollto-next';
  import ExtLink from '$lib/widget/ExtLink.svelte';
  import WebappTitle from '../WebappTitle.svelte';
  import WebappServerInstall from '../WebappServerInstall.svelte';
  import WebappConfigRun from '../WebappConfigRun.svelte';
  import WebappAdditionalInformation from '../WebappAdditionalInformation.svelte';
  import WebappPortForward from '../WebappPortForward.svelte';
</script>


<WebappTitle module="valheim" serverName="Valheim">
  <p>
    <ExtLink href="https://www.valheimgame.com" notranslate>Valheim</ExtLink>
    is a survival game set in a procedurally generated 3D open world sandbox.
    Explore, forage, hunt, mine materials, build shelters and fight enemies to survive in the Viking themed afterlife.
  </p>
  <p>
    This guide will show you how to install, configure and run an Valheim server using this Webapp.
  </p>
  <p>
    Jump to the <a href="#portForwarding" use:scrollto={'#portForwarding'}>Port Forwarding</a>
    section at the end for information on ports.
  </p>
</WebappTitle>
<WebappServerInstall module="valheim" />
<WebappConfigRun />
<WebappAdditionalInformation />
<WebappPortForward serverName="Valheim" configName="Launch Options"
  portsList={[{ purpose: 'Server', port: 2456, protocal: 'UDP' }, { purpose: 'Query', port: 2457, protocal: 'UDP' }]}>
&quot;_comment_upnp&quot;: &quot;Try to automatically redirect ports on home network using UPnP&quot;,
&quot;upnp&quot;: false
</WebappPortForward>
