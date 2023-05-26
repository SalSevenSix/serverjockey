<script>
  import { onMount } from 'svelte';
  import { closeModal } from 'svelte-modals';
  import { notifyError } from '$lib/notifications';
  import { baseurl, securityToken } from '$lib/serverjockeyapi';

  export let isOpen;
  let token = '';

  function kpLogin(event) {
    if (event.key === 'Enter') { login(); }
  }

  function login() {
    if (!token) return notifyError('No token entered');
    fetch(baseurl + '/login', { method: 'post', credentials: 'same-origin', headers: { 'X-Secret': token } })
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        securityToken.set(token);
        if (typeof(Storage) !== 'undefined') {
          sessionStorage.setItem('sjgmsSecurityToken', token);
        }
        closeModal();
      })
      .catch(function(error) { notifyError('Wrong. Please wait 5 seconds before trying again.'); });
  }

  onMount(function() {
    if (typeof(Storage) === 'undefined') return;
    let storedToken = sessionStorage.getItem('sjgmsSecurityToken');
    if (storedToken) { token = storedToken; }
  });
</script>


<div class="modal" class:is-active={isOpen}>
  <div class="modal-background"></div>
  <div class="modal-content">
    <div class="box">
      <div class="field">
        <label for="loginModalToken" class="label">Enter Login Token</label>
        <div class="control">
          <input id="loginModalToken" class="input" type="text" on:keypress={kpLogin} bind:value={token}>
        </div>
      </div>
      <div class="field">
        <div class="control">
          <button name="login" title="Login" class="button is-primary is-fullwidth" on:click={login}>
            <i class="fa fa-right-to-bracket fa-lg"></i>&nbsp;&nbsp;Login</button>
        </div>
      </div>
    </div>
  </div>
</div>
