<script>
  import { scrollto } from 'svelte-scrollto-next';
  import ExtLink from '$lib/widget/ExtLink.svelte';
  import WebappTitle from '$lib/guides/common/WebappTitle.svelte';
  import WebappServerInstall from '$lib/guides/common/WebappServerInstall.svelte';
  import WebappConfigRun from '$lib/guides/common/WebappConfigRun.svelte';
  import WebappGenerateConfig from '$lib/guides/common/WebappGenerateConfig.svelte';
  import WebappAdditionalInformation from '$lib/guides/common/WebappAdditionalInformation.svelte';
  import WebappPortForward from '$lib/guides/common/WebappPortForward.svelte';
</script>


<WebappTitle module="hytale" serverName="Hytale">
  <p>
    <ExtLink href="https://hytale.com" notranslate>Hytale</ExtLink>
    is a voxel based open sandbox game heavily inspired by Minecraft, but with a bigger focus on RPG style adventure.
    This guide will show you how to install, configure and run an Hytale server using this Webapp.
  </p>
  <p>
    Jump to the <a href="#portForwarding" use:scrollto={'#portForwarding'}>Port Forwarding</a>
    section at the end for information on ports.
  </p>
</WebappTitle>
<WebappServerInstall module="hytale" />
<WebappGenerateConfig />
<WebappConfigRun />
<WebappAdditionalInformation />
<WebappPortForward serverName="Hytale" configName="Command Line Args"
  portsList={[{ purpose: 'Server', port: 5520, protocal: 'UDP' }]}>
&quot;_comment_server_upnp&quot;: &quot;Try to automatically redirect server port on home network using UPnP&quot;,
&quot;server_upnp&quot;: false
</WebappPortForward>
