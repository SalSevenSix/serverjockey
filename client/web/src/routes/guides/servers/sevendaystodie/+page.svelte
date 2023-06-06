<script>
  import { scrollto } from 'svelte-scrollto-element';
  import BackToTop from '$lib/BackToTop.svelte';
  import WebappServerInstall from '../WebappServerInstall.svelte';
  import WebappConfigRun from '../WebappConfigRun.svelte';
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

<div class="content" id="portForwarding">
  <h4 class="title is-5">Port Forwarding</h4>
  <p>
    7 Days to Die requires the ports shown below to be open and redirected. However if you are using a home network,
    the server does not automatically redirect ports behind a NAT. Please read the
    <a href="https://developer.valvesoftware.com/wiki/7_Days_to_Die_Dedicated_Server#Firewall_Ports" target="_blank">
      ports section <i class="fa fa-up-right-from-square"></i></a>
    on the dedicated server wiki page for more help on ports.
  </p>
  <table class="table is-thinner">
    <thead>
      <tr><th>Purpose</th><th>Ports</th><th>Protocal</th></tr>
    </thead>
    <tbody class="is-family-monospace">
      <tr><td>Main</td><td>26900</td><td>TCP and UDP</td></tr>
      <tr><td>Additional</td><td>26901-26903</td><td>UDP</td></tr>
      <tr><td>Webcon (optional)</td><td>8080</td><td>TCP</td></tr>
      <tr><td>Telnet (optional)</td><td>8081</td><td>TCP</td></tr>
    </tbody>
  </table>
</div>

<BackToTop />
