<script>
  import { onDestroy, tick } from 'svelte';
  import { fade } from 'svelte/transition';
  import { closeModal } from 'svelte-modals';
  import { sleep, RollingLog } from '$lib/util/util';
  import { SubscriptionHelper, newPostRequest } from '$lib/util/sjgmsapi';
  import { notifyError } from '$lib/util/notifications';
  import InputText from '$lib/widget/InputText.svelte';
  import InputPassword from '$lib/widget/InputPassword.svelte';

  const subs = new SubscriptionHelper();
  const logLines = new RollingLog();

  export let isOpen;
  export let instance;
  export let onSuccess;

  let stage = 0;  // 0=ready 1=start 2=pass 3=code
  let steamLogin;
  let steamPassword;
  let steamCode;
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
      await fetch(instance.url('/steamcmd/input'), newPostRequest());
    }
  }

  function kpStartLogin(event) {
    if (event.key === 'Enter') { startLogin(); }
  }

  function startLogin() {
    if (!steamLogin) {
      notifyError('Login not provided');
      return;
    }
    stage = 1;
    heartbeat();
    const request = newPostRequest();
    request.body = JSON.stringify({ login: steamLogin });
    fetch(instance.url('/steamcmd/login'), request)
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        subs.poll(json.url, function(data) {
          logText = logLines.append(data).toText();
          if (data.includes('Cached credentials not found')) { stage = 2; }
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

  function kpEnterPassword(event) {
    if (event.key === 'Enter') { enterPassword(); }
  }

  function enterPassword() {
    if (!steamPassword) {
      notifyError('Password not provided');
      return;
    }
    const request = newPostRequest();
    request.body = JSON.stringify({ value: steamPassword });
    fetch(instance.url('/steamcmd/input'), request)
      .then(function(response) { if (!response.ok) throw new Error('Status: ' + response.status); })
      .catch(function(error) { notifyError('Failed to send password.'); });
  }

  function kpEnterCode(event) {
    if (event.key === 'Enter') { enterCode(); }
  }

  function enterCode() {
    if (!steamCode) {
      notifyError('Code not provided');
      return;
    }
    const request = newPostRequest();
    request.body = JSON.stringify({ value: steamCode });
    fetch(instance.url('/steamcmd/input'), request)
      .then(function(response) { if (!response.ok) throw new Error('Status: ' + response.status); })
      .catch(function(error) { notifyError('Failed to send code.'); });
  }

  onDestroy(function() {
    stage = 0;
    subs.stop();
  });
</script>


<div class="modal" class:is-active={isOpen}>
  <div class="modal-background" role="button" tabindex="0" on:click={closeModal} on:keypress={function() {}}></div>
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
        <div class="block">
          <InputText id="steamLoginModalLogin" label="Steam Login" bind:value={steamLogin}
                     disabled={stage > 0} onKeypress={kpStartLogin} nowrap autofocus />
          <div class="field buttons is-right">
            <button id="steamLoginModalLoginSubmit" title="Login Steam" class="button is-primary"
                    disabled={stage > 0} on:click={startLogin}>
              <i class="fa fa-right-to-bracket fa-lg"></i>&nbsp;&nbsp;Login</button>
          </div>
        </div>
      {:else if stage == 2}
        <div class="block" in:fade={{ duration: 500 }}>
          <InputPassword id="steamLoginModalPassword" label="Enter Password" bind:value={steamPassword}
                         onKeypress={kpEnterPassword} nowrap autofocus />
          <div class="field buttons is-right">
            <button id="steamLoginModalPasswordSubmit" title="Enter Password" class="button is-primary"
                    on:click={enterPassword}>
              <i class="fa fa-arrow-right fa-lg"></i>&nbsp;&nbsp;Enter</button>
          </div>
        </div>
      {:else if stage == 3}
        <div class="block" in:fade={{ duration: 500 }}>
          <InputText id="steamLoginModalCode" label="Enter Steam Guard Code" bind:value={steamCode}
                     onKeypress={kpEnterCode} nowrap autofocus />
          <div class="field buttons is-right">
            <button id="steamLoginModalCodeSubmit" title="Enter Code" class="button is-primary"
                    on:click={enterCode}>
              <i class="fa fa-arrow-right fa-lg"></i>&nbsp;&nbsp;Enter</button>
          </div>
        </div>
      {/if}
      <div class="block field">
        <div class="control">
          <textarea id="steamLoginModalLog" class="textarea has-fixed-size is-family-monospace is-size-7" rows="4"
                    bind:this={logBox} readonly>{logText}</textarea>
        </div>
      </div>
    </section>
  </div>
</div>
