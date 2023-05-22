<script>
  import { notifyError } from '$lib/notifications';
  import { onDestroy, tick } from 'svelte';
  import { closeModal } from 'svelte-modals';
  import { sleep, RollingLog } from '$lib/util';
  import { instance, SubscriptionHelper, newPostRequest } from '$lib/serverjockeyapi';

  export let isOpen;
  export let onSuccess;

  let subs = new SubscriptionHelper();
  let stage = 0;  // 0=ready 1=start 2=pass 3=code
  let steamLogin;
  let steamPassword;
  let steamCode;
  let logLines = new RollingLog();
  let logText = '';
  let logBox;

  $: if (logText && logBox) {
    tick().then(function() {
      logBox.scroll({ top: logBox.scrollHeight });
    });
  }

  async function heartbeat() {
    while (stage > 0) {
      await sleep(1000);
      await fetch($instance.url + '/steamcmd/input', newPostRequest());
    }
  }

  function startLogin() {
    if (!steamLogin) {
      notifyError('Login not provided');
      return;
    }
    stage = 1;
    heartbeat();
    let request = newPostRequest();
    request.body = JSON.stringify({ login: steamLogin });
    fetch($instance.url + '/steamcmd/login', request)
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        subs.poll(json.url, function(data) {
          logText = logLines.append(data).toText();
          if (data.includes('Logging in user \'' + steamLogin + '\' to Steam Public...')) { stage = 2; }
          if (data.includes('Enter the current code from your Steam Guard Mobile Authenticator app')) { stage = 3; }
          return true;
        })
        .then(function() {
          closeModal();
          if (logText.includes('Waiting for user info...OK')) { onSuccess(); }
        })
        .finally(function() { stage = 0; });
      })
      .catch(function(error) {
        notifyError('Failed to login to Steam.');
        stage = 0;
      });
  }

  function enterPassword() {
    if (!steamPassword) {
      notifyError('Password not provided');
      return;
    }
    let request = newPostRequest();
    request.body = JSON.stringify({ value: steamPassword });
    fetch($instance.url + '/steamcmd/input', request)
      .then(function(response) { if (!response.ok) throw new Error('Status: ' + response.status); })
      .catch(function(error) { notifyError('Failed to send password.'); });
  }

  function enterCode() {
    if (!steamCode) {
      notifyError('Code not provided');
      return;
    }
    let request = newPostRequest();
    request.body = JSON.stringify({ value: steamCode });
    fetch($instance.url + '/steamcmd/input', request)
      .then(function(response) { if (!response.ok) throw new Error('Status: ' + response.status); })
      .catch(function(error) { notifyError('Failed to send code.'); });
  }

  onDestroy(function() {
    stage = 0;
    subs.stop();
  });
</script>


<div class="modal" class:is-active={isOpen}>
  <div class="modal-background" on:click={closeModal} on:keypress={function() {}}></div>
  <div class="modal-card">
    <header class="modal-card-head">
      <p class="modal-card-title">Login to Steam</p>
      <button class="delete is-large" aria-label="close" on:click={closeModal}></button>
    </header>
    <section class="modal-card-body">
      <div class="content">
        <p>This game server requires a Steam account with game licence to install.
           Please provide Steam credentials to continue.</p>
      </div>
      {#if stage < 2}
        <div class="field">
          <label for="steamLoginModalLogin" class="label">Steam Login</label>
          <div class="control">
            <input id="steamLoginModalLogin" class="input" type="text" bind:value={steamLogin} />
          </div>
        </div>
        <div class="field buttons is-right">
          <button name="steam-login-start" title="Login Steam" class="button is-primary"
                  disabled={stage > 0} on:click={startLogin}>
            <i class="fa fa-right-to-bracket fa-lg"></i>&nbsp;&nbsp;Login</button>
        </div>
      {/if}
      {#if stage == 2}
        <div class="field">
          <label for="steamLoginModalPassword" class="label">Enter Password</label>
          <div class="control">
            <input id="steamLoginModalPassword" class="input" type="password" bind:value={steamPassword} />
          </div>
        </div>
        <div class="field buttons is-right">
          <button name="steam-password-enter" title="Enter Password" class="button is-primary" on:click={enterPassword}>
            <i class="fa fa-arrow-right fa-lg"></i>&nbsp;&nbsp;Enter</button>
        </div>
      {/if}
      {#if stage == 3}
        <div class="field">
          <label for="steamLoginModalCode" class="label">Enter Steam Guard Code</label>
          <div class="control">
            <input id="steamLoginModalCode" class="input" type="text" bind:value={steamCode} />
          </div>
        </div>
        <div class="field buttons is-right">
          <button name="steam-code-enter" title="Enter Code" class="button is-primary" on:click={enterCode}>
            <i class="fa fa-arrow-right fa-lg"></i>&nbsp;&nbsp;Enter</button>
        </div>
      {/if}
      <div class="field">
        <div class="control">
          <textarea class="textarea has-fixed-size is-family-monospace is-size-7" rows="4"
                    bind:this={logBox} readonly>{logText}</textarea>
        </div>
      </div>
    </section>
  </div>
</div>
