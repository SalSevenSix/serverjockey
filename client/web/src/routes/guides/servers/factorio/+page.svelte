<script>
  import { scrollto } from 'svelte-scrollto-element';
  import BackToTop from '$lib/BackToTop.svelte';
  import WebappServerInstall from '../WebappServerInstall.svelte';
  import WebappConfigRun from '../WebappConfigRun.svelte';
</script>


<div class="columns">
  <div class="column is-one-quarter">
    <figure class="image pt-3"><img src="/assets/icons/ft_icon.jpg" alt="Factorio icon" /></figure>
  </div>
  <div class="column is-three-quarters content">
    <h2 class="title is-3 mt-2">Factorio</h2>
    <p>
      <a href="https://www.factorio.com" target="_blank">Factorio <i class="fa fa-up-right-from-square"></i></a>
      is a game where you build, maintain and protect a factory. This involves mining resources,
      researching technologies, building infrastructure, automating production, and fighting enemies.
    </p>
    <p>
      This guide will show you how to install, configure and run a Factorio server using this Webapp.
    </p>
    <p>
      Jump to the <a href="#portForwarding" use:scrollto={'#portForwarding'}>Port Forwarding</a>
      section at the end for information on ports.
    </p>
  </div>
</div>

<WebappServerInstall module="factorio" />
<WebappConfigRun />

<div class="content" id="additionalInformation">
  <hr />
  <h3 class="title is-4">Additional Information</h3>
</div>

<div class="content" id="portForwarding">
  <h4 class="title is-5">Port Forwarding</h4>
  <p>
    Factorio only needs a single port opened and redirected for UDP traffic.
    However if you are using a home network, the server does not automatically redirect ports behind a NAT.
    Please read the
    <a href="https://wiki.factorio.com/Multiplayer#Connecting_to_a_Server_Behind_NAT" target="_blank">
      multiplayer information <i class="fa fa-up-right-from-square"></i></a>
    on the Factorio wiki for help on how to redirect ports.
  </p>
  <table class="table is-thinner">
    <thead>
      <tr><th>Purpose</th><th>Port</th><th>Protocal</th></tr>
    </thead>
    <tbody class="is-family-monospace">
      <tr><td>Server</td><td>34197</td><td>UDP</td></tr>
    </tbody>
  </table>
</div>

<BackToTop />
