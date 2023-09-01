<script>
  import { scrollto } from 'svelte-scrollto-element';
  import BackToTop from '$lib/BackToTop.svelte';
  import WebappServerInstall from '../WebappServerInstall.svelte';
  import WebappConfigRun from '../WebappConfigRun.svelte';
  import WebappGenerateConfig from '../WebappGenerateConfig.svelte';
  import WebappPortForward from '../WebappPortForward.svelte';
</script>


<div class="columns">
  <div class="column is-one-quarter">
    <figure class="image pt-3"><img src="/assets/icons/ut_icon.jpg" alt="Unturned icon" /></figure>
  </div>
  <div class="column is-three-quarters content">
    <h2 class="title is-3 mt-2">Unturned</h2>
    <p>
      <a href="https://smartlydressedgames.com" target="_blank">Unturned <i class="fa fa-up-right-from-square"></i></a>
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
  </div>
</div>

<WebappServerInstall module="unturned" />
<WebappGenerateConfig />
<WebappConfigRun />

<div class="content" id="additionalInformation">
  <hr />
  <h3 class="title is-4">Additional Information</h3>
</div>

<WebappPortForward serverName="Starbound" configName="Launch Options"
  portsList={[{ purpose: 'Queries', port: 27015, protocal: 'UDP' }, { purpose: 'Server', port: 27016, protocal: 'UDP' }]}>
&quot;_comment_upnp&quot;: &quot;Try to automatically redirect ports on home network using UPnP&quot;,
&quot;upnp&quot;: false
</WebappPortForward>

<BackToTop />
