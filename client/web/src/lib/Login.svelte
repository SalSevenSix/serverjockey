<script>
  import { notifyError } from '$lib/notifications';
  import { baseurl, securityToken } from '$lib/serverjockeyapi';

  let token = '';
	function login() {
    if (!token) return notifyError('No token entered');
    fetch(baseurl + '/login', { method: 'post', credentials: 'same-origin', headers: { 'X-Secret': token } })
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        securityToken.set(token);
      })
      .catch(function(error) { notifyError('Wrong.'); });
	}
</script>


<div class="columns is-centered">
  <div class="column is-half">
    <div class="box">
      <div class="field">
        <label for="login-token" class="label">Enter Login Token</label>
        <div class="control">
          <input id="login-token" class="input" type="text" bind:value={token} />
        </div>
      </div>
      <div class="field">
        <div class="control">
          <button id="login" name="login" class="button is-primary is-fullwidth" on:click={login}>Login</button>
        </div>
      </div>
    </div>
  </div>
</div>
