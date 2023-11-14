<script>
  import { onDestroy, getContext } from 'svelte';
  import { notifyInfo, notifyWarning, notifyError } from '$lib/notifications';
  import { confirmModal, steamLoginModal } from '$lib/modals';
  import { RollingLog } from '$lib/util';
  import { SubscriptionHelper, newPostRequest, openFileInNewTab } from '$lib/sjgmsapi';

  const instance = getContext('instance');
  const serverStatus = getContext('serverStatus');
  const subs = new SubscriptionHelper();
  const logLines = new RollingLog();

  export let qualifierName = null;

  let qualifier = '';
  let endInstallMessage = 'Install Runtime completed. Please check console log output for details.';

  $: cannotProcess = $serverStatus.running || $serverStatus.state === 'MAINTENANCE';

  function runtimeMeta() {
    openFileInNewTab(instance.url('/deployment/runtime-meta'), function(error) {
      notifyWarning('Meta not found. No runtime installed.');
    });
  }

  function wipeRuntime() {
    confirmModal('Are you sure you want to Delete Runtime ?', function() {
      cannotProcess = true;
      fetch(instance.url('/deployment/wipe-runtime'), newPostRequest())
        .then(function(response) {
          if (!response.ok) throw new Error('Status: ' + response.status);
          notifyInfo('Delete runtime completed.');
        })
        .catch(function(error) { notifyError('Delete Runtime failed.'); })
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
    fetch(instance.url('/deployment/install-runtime'), request)
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
              steamLoginModal(instance, doInstallRuntime);
            } else {
              notifyInfo(endInstallMessage);
            }
          });
        } else if (json) {
          notifyInfo('Install Runtime completed.');
          cannotProcess = false;
        } else {
          steamLoginModal(instance, doInstallRuntime);
          cannotProcess = false;
        }
      })
      .catch(function(error) {
        notifyError('Failed to Install Runtime.');
        cannotProcess = false;
      });
  }

  onDestroy(function() {
    endInstallMessage = 'Please check console log output for install results.';
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
      <label for="installRuntimeQualifier" class="label"
             title="Set to appropriate version/beta/tag to install desired non-stable version">
        {qualifierName}</label>
      <div class="control pr-6">
        <input id="installRuntimeQualifier" class="input" type="text"
               disabled={cannotProcess} bind:value={qualifier}>
      </div>
    </div>
  {/if}
  <div class="field">
    <div class="control buttons">
      <button name="wipe-runtime" title="Delete Runtime" class="button is-danger"
              disabled={cannotProcess} on:click={wipeRuntime}>
        <i class="fa fa-trash-can fa-lg"></i>&nbsp;&nbsp;Delete Runtime</button>
      <button name="install-runtime" title="Install Runtime" class="button is-warning"
              disabled={cannotProcess} on:click={installRuntime}>
        <i class="fa fa-gear fa-lg"></i>&nbsp;&nbsp;Install Runtime</button>
      <button name="runtime-meta" title="Runtime Runtime" class="button is-primary"
              on:click={runtimeMeta}>
        <i class="fa fa-circle-info fa-lg"></i>&nbsp;&nbsp;Runtime Meta</button>
    </div>
  </div>
</div>
