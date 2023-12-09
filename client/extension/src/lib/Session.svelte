<script>
  import { onMount } from 'svelte';
  import { connection, logError } from '$lib/sjgmsapi';
  import Login from '$lib/Login.svelte';
  import Logout from '$lib/Logout.svelte';

  const urlKey = 'sjgmsExtensionUrl';
  const tokenKey = 'sjgmsExtensionToken';
  const noStorage = typeof(Storage) === 'undefined';

  let checking = true;
  let url = '';
  let token = '';

  function disconnect() {
    url = '';
    token = '';
    $connection = null;
    if (noStorage) return;
    localStorage.removeItem(tokenKey);
    localStorage.removeItem(urlKey);
  }

  function connect(cUrl, cToken) {
    $connection = null;
    while (cUrl.endsWith('/')) { cUrl = cUrl.substring(0, cUrl.length - 1); }
    return fetch(cUrl + '/login', { method: 'post', headers: { 'X-Secret': cToken } })  // credentials: 'same-origin'
      .then(function(response) {
        if (!response.ok) { throw new Error('Status: ' + response.status); }
        url = cUrl;
        token = cToken;
        $connection = { url: url, token: token };
        if (noStorage) return;
        localStorage.setItem(urlKey, url);
        localStorage.setItem(tokenKey, token);
      })
      .catch(function(error) {
        token = '';
        logError(error);
        if (noStorage) return;
        localStorage.removeItem(tokenKey);
      });
  }

  onMount(function() {
    if (noStorage) {
      checking = false;
      return;
    }
    let storedUrl = localStorage.getItem(urlKey);
    if (storedUrl) { url = storedUrl; }
    let storedToken = localStorage.getItem(tokenKey);
    if (storedToken) { token = storedToken; }
    if (url && token) {
      connect(url, token).finally(function() { checking = false; });
    } else {
      checking = false;
    }
  });
</script>


{#if checking}
  <p>loading ...</p>
{:else}
  {#if $connection}
    <Logout {disconnect} />
    <slot />
  {:else}
    <Login {url} {token} {connect} />
  {/if}
{/if}
