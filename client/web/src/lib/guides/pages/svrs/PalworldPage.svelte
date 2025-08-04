<script>
  import { scrollto } from 'svelte-scrollto-next';
  import ExtLink from '$lib/widget/ExtLink.svelte';
  import WebappTitle from '$lib/guides/common/WebappTitle.svelte';
  import WebappServerInstall from '$lib/guides/common/WebappServerInstall.svelte';
  import WebappConfigRun from '$lib/guides/common/WebappConfigRun.svelte';
  import WebappAdditionalInformation from '$lib/guides/common/WebappAdditionalInformation.svelte';
  import WebappPortForward from '$lib/guides/common/WebappPortForward.svelte';

  const portsList = [{ purpose: 'Server', port: '8211', protocal: 'UDP' },
                     { purpose: 'Query', port: '27015', protocal: 'UDP' },
                     { purpose: 'Rcon', port: '25575', protocal: 'TCP' }];
</script>


<WebappTitle module="palworld" serverName="Palworld">
  <p>
    <ExtLink href="https://www.pocketpair.jp/palworld" notranslate>Palworld</ExtLink>
    is a monster-catching, survival and crafting game, but incorporates a variety of mechanics from other genres in
    order to provide a new experience for everyone. Fight, farm, build and work alongside mysterious creatures called
    &quot;Pals&quot; in a multiplayer open world survival and crafting game.
  </p>
  <p>
    This guide will show you how to install, configure and run a Palworld server using this Webapp.
  </p>
  <p>
    Jump to the <a href="#portForwarding" use:scrollto={'#portForwarding'}>Port Forwarding</a>
    section at the end for information on ports.
  </p>
</WebappTitle>
<WebappServerInstall module="palworld" />
<WebappConfigRun />
<WebappAdditionalInformation />
<WebappPortForward serverName="Palworld" configName="Launch Options" portsList={portsList}>
&quot;_comment_server_upnp&quot;: &quot;Try to automatically redirect server port on home network using UPnP.&quot;,
&quot;server_upnp&quot;: false,
&quot;_comment_query_upnp&quot;: &quot;Try to automatically redirect query port on home network using UPnP.&quot;,
&quot;query_upnp&quot;: false,
&quot;_comment_rcon_upnp&quot;: &quot;Try to automatically redirect rcon port on home network using UPnP.&quot;,
&quot;rcon_upnp&quot;: false
</WebappPortForward>
