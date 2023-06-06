<script>
  import { scrollto } from 'svelte-scrollto-element';
  import BackToTop from '$lib/BackToTop.svelte';
  import WebappServerInstall from '../WebappServerInstall.svelte';
  import WebappConfigRun from '../WebappConfigRun.svelte';
  import WebappGenerateConfig from '../WebappGenerateConfig.svelte';
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

<div class="content" id="portForwarding">
  <h4 class="title is-5">Port Forwarding</h4>
  <p>
    Unturned requires the ports shown below to be open and redirected. However if you are using a home network,
    the server does not automatically redirect ports behind a NAT. Please read the
    <a href="https://docs.smartlydressedgames.com/en/stable/servers/port-forwarding.html" target="_blank">
      port forwarding page <i class="fa fa-up-right-from-square"></i></a> on the docs website for more help on ports.
  </p>
  <table class="table is-thinner">
    <thead>
      <tr><th>Purpose</th><th>Port</th><th>Protocal</th></tr>
    </thead>
    <tbody class="is-family-monospace">
      <tr><td>Queries</td><td>27015</td><td>UDP</td></tr>
      <tr><td>Server</td><td>27016</td><td>UDP</td></tr>
    </tbody>
  </table>
</div>

<BackToTop />
