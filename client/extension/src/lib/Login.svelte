<script>
  export let url = '';
  export let token = '';
  export let connect;

  let connecting = false;

  $: cannotConnect = !url || !token || connecting;

  function click() {
    connecting = true;
    connect(url, token).finally(function() { connecting = false; });
  }
</script>


<div>
  <p>Connect to your ServerJockey system...</p>
  <label for="serverJockeyUrl">URL</label><br />
  <input id="serverJockeyUrl" class="input" type="text" bind:value={url}><br />
  <label for="serverJockeyToken">Token</label><br />
  <input id="serverJockeyToken" class="input" type="text" bind:value={token}><br />
  <button name="login" title="Login" disabled={cannotConnect} on:click={click}>Connect</button>
</div>
