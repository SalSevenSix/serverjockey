<script>
  export let sectionId = 'portForwarding';
  export let upnpService = 'ServerJockey';
  export let serverName;
  export let configName;
  export let portsList;  // [{ purpose: '', port: 0, protocal: 'TCP' }]
</script>


<div class="content" id={sectionId}>
  <h4 class="title is-5">Port Forwarding</h4>
  <p>
    In order for people to connect to your {serverName} server over the internet, your home
    router (internet gateway / &quot;modem&quot;) needs to be configured to forward ports to the server.
    <span class="is-italic">By default {upnpService} will automatically forward ports using UPnP.</span>
    However, if this is not working on your LAN, you can manually add the port forwarding.
  </p>
  <p>
    To do this, login to your router then forward ports as shown below. Use the local IP address as shown on the
    ServerJockey webapp home page. More detailed instructions cannot be provided because each router will have
    a different webapp interface depending on the brand and model.
  </p>
  <table class="table is-thinner">
    <thead>
      <tr><th>Purpose</th><th>Port</th><th>Protocal</th></tr>
    </thead>
    <tbody class="is-family-monospace">
    {#each portsList as portData}
      <tr><td>{portData.purpose}</td><td>{portData.port}</td><td>{portData.protocal}</td></tr>
    {/each}
    </tbody>
  </table>
  <p>
    If using manual port forwarding you should also disable UPnP in the
    <span class="has-text-weight-bold">{configName}</span> configuration.
  </p>
  <pre class="pre is-thinner"><slot /></pre>
</div>
