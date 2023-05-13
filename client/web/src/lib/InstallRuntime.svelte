<script>
  import { onDestroy } from 'svelte';
  import { notifyInfo, notifyWarning, notifyError } from '$lib/notifications';
  import { confirmModal, steamLoginModal } from '$lib/modals';
  import { RollingLog } from '$lib/util';
  import { instance, serverStatus, SubscriptionHelper, newPostRequest, openFileInNewTab } from '$lib/serverjockeyapi';

  export let qualifierName = null;
  let subs = new SubscriptionHelper();
  let logLines = new RollingLog();
  let qualifier = '';

  $: cannotProcess = $serverStatus.running || $serverStatus.state === 'MAINTENANCE';

  function runtimeMeta() {
    openFileInNewTab($instance.url + '/deployment/runtime-meta', function(error) {
      notifyWarning('Meta not found. No runtime installed.');
    });
  }

  function wipeRuntime() {
    confirmModal('Are you sure you want to delete runtime ?', function() {
      cannotProcess = true;
      fetch($instance.url + '/deployment/wipe-runtime', newPostRequest())
        .then(function(response) {
          if (!response.ok) throw new Error('Status: ' + response.status);
          notifyInfo('Delete runtime completed.');
        })
        .catch(function(error) { notifyError('Delete runtime failed.'); })
        .finally(function() { cannotProcess = false; });
    });
  }

  function installRuntime() {
    confirmModal(
      'Are you sure you want to Install Runtime ?\nAny existing install will be updated.',
      doInstallRuntime);
  }

  function doInstallRuntime() {
    cannotProcess = true;
    let request = newPostRequest();
    let body = { wipe: false, validate: true };
    if (qualifier) { body.beta = qualifier; }
    request.body = JSON.stringify(body);
    fetch($instance.url + '/deployment/install-runtime', request)
      .then(function(response) {
        if (response.status === 204) return true;
        if (response.status === 409) return false;
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        if (json && json.url) {
          subs.poll(json.url, function(data) {
            logLines.append(data);
            return true;
          })
          .finally(function() {
            if (logLines.toText().includes('password:')) {
              logLines.reset();
              steamLoginModal(doInstallRuntime);
            } else {
              notifyInfo('Install Runtime completed. Please check console log output for details.');
            }
          });
        } else if (json) {
          notifyInfo('Install Runtime completed.');
          cannotProcess = false;
        } else {
          steamLoginModal(doInstallRuntime);
          cannotProcess = false;
        }
      })
      .catch(function(error) {
        notifyError('Failed to Install Runtime.');
        cannotProcess = false;
      });
  }

  onDestroy(function() {
    subs.stop();
  });
</script>


<div class="content">
  <p>
    Please be patient with the Install Runtime process, it may take a while. Check the console log to confirm success.
  </p>
</div>

<div class="block">
  {#if qualifierName}
    <div class="field">
      <label for="install-runtime-qualifier" class="label">{qualifierName}</label>
      <div class="control">
        <input id="install-runtime-qualifier" class="input" type="text" bind:value={qualifier}>
      </div>
    </div>
  {/if}
  <div class="field">
    <div class="control buttons">
      <button id="wipe-runtime" name="wipe-runtime" class="button is-danger"
              disabled={cannotProcess} on:click={wipeRuntime}>Delete Runtime</button>
      <button id="install-runtime" name="install-runtime" class="button is-warning"
              disabled={cannotProcess} on:click={installRuntime}>Install Runtime</button>
      <button id="runtime-meta" name="runtime-meta" class="button is-primary"
              disabled={cannotProcess} on:click={runtimeMeta}>Runtime Meta</button>
    </div>
  </div>
</div>
