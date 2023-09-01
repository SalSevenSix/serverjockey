<script>
  import { scrollto } from 'svelte-scrollto-element';
  import BackToTop from '$lib/BackToTop.svelte';
  import WebappServerInstall from '../WebappServerInstall.svelte';
  import WebappConfigRun from '../WebappConfigRun.svelte';
  import WebappPortForward from '../WebappPortForward.svelte';

  let portsList=[{ purpose: 'Main', port: '26900', protocal: 'TCP and UDP' },
                 { purpose: 'Additional', port: '26901-26903', protocal: 'UDP' },
                 { purpose: 'Webcon (optional)', port: '8080', protocal: 'TCP' },
                 { purpose: 'Telnet (optional)', port: '8081', protocal: 'TCP' }];
</script>


<div class="columns">
  <div class="column is-one-quarter">
    <figure class="image pt-3"><img src="/assets/icons/7d2d_icon.png" alt="7d2d icon" /></figure>
  </div>
  <div class="column is-three-quarters content">
    <h2 class="title is-3 mt-2">7 Days to Die</h2>
    <p>
      <a href="https://7daystodie.com" target="_blank">7 Days to Die <i class="fa fa-up-right-from-square"></i></a>
      is zombie apocalypse survival horror game set in a 3D open world. It features combat, looting, mining, crafting,
      base building &amp; defence, exploration, and RPG elements.
    </p>
    <p>
      This guide will show you how to install, configure and run a 7 Days to Die server using this Webapp.
    </p>
    <p>
      Jump to the <a href="#portForwarding" use:scrollto={'#portForwarding'}>Port Forwarding</a>
      section at the end for information on ports.
    </p>
  </div>
</div>

<WebappServerInstall module="sevendaystodie" />
<WebappConfigRun />

<div class="content" id="additionalInformation">
  <hr />
  <h3 class="title is-4">Additional Information</h3>
</div>

<WebappPortForward serverName="7 Days to Die" configName="Launch Options" portsList={portsList}>
&quot;_comment_server_upnp&quot;: &quot;Try to automatically redirect server ports on home network using UPnP&quot;,
&quot;server_upnp&quot;: false,
&quot;_comment_console_upnp&quot;: &quot;Try to automatically redirect web console port on home network using UPnP&quot;,
&quot;console_upnp&quot;: false,
&quot;_comment_telnet_upnp&quot;: &quot;Try to automatically redirect telnet port on home network using UPnP&quot;,
&quot;telnet_upnp&quot;: false
</WebappPortForward>

<BackToTop />
