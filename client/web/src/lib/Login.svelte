<script>
  import { doLogin } from '$lib/serverjockeyapi';

  let value = '';
	function login() {
	  doLogin(value);
	}
</script>


<div class="block">
  <h1 class="title is-2">ZomBox</h1>
  <h1 class="subtitle">ServerJockey system v0.1</h1>
</div>

<div class="columns is-centered">
  <div class="column is-half">
    <div class="box">
      <div class="field">
        <label for="login-token" class="label">Enter Login Token</label>
        <div class="control">
          <input id="login-token" class="input" type="text" bind:value={value} />
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
