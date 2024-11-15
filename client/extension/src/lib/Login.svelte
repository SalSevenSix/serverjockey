<script>
  export let url = '';
  export let token = '';
  export let connect;

  let connecting = false;

  $: cannotConnect = !url || !token || connecting;

  function kpConnect(event) {
    if (event.key === 'Enter') { doConnect(); }
  }

  function doConnect() {
    if (cannotConnect) return;
    connecting = true;
    connect(url, token).finally(function() { connecting = false; });
  }
</script>


<div>
  <p>Connect to your ServerJockey system...</p>
  <h2>URL</h2>
  <input class="input" type="text" bind:value={url}>
  <h2>Token</h2>
  <input class="input" type="text" bind:value={token} on:keypress={kpConnect}>
  <p>
    <button class="process hero" disabled={cannotConnect} on:click={doConnect}>Connect</button>
  </p>
</div>
