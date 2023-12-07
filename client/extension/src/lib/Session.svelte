<script>
  import { onMount } from 'svelte';
  import { connection } from '$lib/sjgmsapi';
  import Login from '$lib/Login.svelte';

  const urlKey = 'sjgmsExtensionUrl';
  const tokenKey = 'sjgmsExtensionToken';
  const noStorage = typeof(Storage) === 'undefined';

  let checking = true;
  let url = '';
  let token = '';

  function connect(cUrl, cToken) {
    $connection = null;
    while (cUrl.endsWith('/')) { cUrl = cUrl.substring(0, cUrl.length - 1); }
    return fetch(cUrl + '/login', { method: 'post', credentials: 'same-origin', headers: { 'X-Secret': cToken } })
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
        console.error(error);
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
    <slot />
  {:else}
    <Login url={url} token={token} connect={connect} />
  {/if}
{/if}
