<script>
  import { onMount } from 'svelte';
  import { closeModal } from 'svelte-modals';
  import { noStorage } from '$lib/util/browserutil';
  import { notifyError } from '$lib/util/notifications';
  import { surl, securityToken } from '$lib/util/sjgmsapi';
  import InputText from '$lib/widget/InputText.svelte';

  class LoginFailed extends Error {
    constructor() {
      super('Wrong. Please wait 5 seconds before trying again. Note that token is reset every system restart.');
      this.name = 'LoginFailed';
    }
  }

  const storageKey = 'sjgmsSecurityToken';

  export let isOpen;

  let remember = false;
  let token = '';

  $: cannotLogin = !token || token.length != 10;

  function kpLogin(event) {
    if (event.key === 'Enter') { login(); }
  }

  function login() {
    if (cannotLogin) return;
    fetch(surl('/login'), { method: 'post', headers: { 'X-Secret': token } })
      .then(function(response) {
        if (response.status === 401) throw new LoginFailed();
        if (!response.ok) throw new Error('Status: ' + response.status);
        securityToken.set(token);
        if (!noStorage) {
          sessionStorage.setItem(storageKey, token);
          if (remember) {
            localStorage.setItem(storageKey, token);
          } else {
            localStorage.removeItem(storageKey);
          }
        }
        closeModal();
      })
      .catch(function(error) {
        notifyError(error.name === 'LoginFailed' ? error.message : 'Login error. Please check connection and server.');
      });
  }

  onMount(function() {
    if (noStorage) return;
    let storedToken = localStorage.getItem(storageKey);
    if (storedToken) {
      token = storedToken;
      remember = true;
      return;
    }
    storedToken = sessionStorage.getItem(storageKey);
    if (storedToken) {
      token = storedToken;
    }
  });
</script>


<div class="modal" class:is-active={isOpen}>
  <div class="modal-background"></div>
  <div class="modal-content">
    <div class="box">
      <InputText id="loginModalToken" label="Login Token" bind:value={token}
                 onKeypress={kpLogin} noautocomplete autofocus />
      <div class="field">
        <div class="control">
          <label class="checkbox">
            <input id="loginModalRemember" type="checkbox" bind:checked={remember}>&nbsp; Remember Token
          </label>
        </div>
      </div>
      <div class="field">
        <div class="control">
          <button id="loginModalLogin" title="Login" class="button is-primary is-fullwidth"
                  disabled={cannotLogin} on:click={login}>
            <i class="fa fa-right-to-bracket fa-lg"></i>&nbsp;&nbsp;Login</button>
        </div>
      </div>
    </div>
  </div>
</div>
