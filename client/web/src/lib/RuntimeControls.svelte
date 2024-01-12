<script>
  import { onDestroy, getContext } from 'svelte';
  import { openModal } from 'svelte-modals';
  import { RollingLog, ObjectUrls } from '$lib/util/util';
  import { SubscriptionHelper, newGetRequest, newPostRequest } from '$lib/util/sjgmsapi';
  import { notifyInfo, notifyWarning, notifyError } from '$lib/util/notifications';
  import { confirmModal } from '$lib/modal/modals';
  import SteamLoginModal from '$lib/SteamLoginModal.svelte';

  const instance = getContext('instance');
  const serverStatus = getContext('serverStatus');
  const subs = new SubscriptionHelper();
  const objectUrls = new ObjectUrls();
  const logLines = new RollingLog();

  export let qualifierName;

  let qualifier = '';
  let endInstallMessage = 'Install Runtime completed. Please check console log output for details.';

  $: cannotProcess = $serverStatus.running || $serverStatus.state === 'MAINTENANCE';

  function runtimeMeta() {
    fetch(instance.url('/deployment/runtime-meta'), newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.blob();
      })
      .then(function(blob) {
        objectUrls.openBlob(blob);
      })
      .catch(function(error) {
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

  function openSteamLoginModal() {
    openModal(SteamLoginModal, { instance: instance, onSuccess: doInstallRuntime });
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
              openSteamLoginModal();
            } else {
              notifyInfo(endInstallMessage);
            }
          });
        } else if (json) {
          notifyInfo('Install Runtime completed.');
          cannotProcess = false;
        } else {
          openSteamLoginModal();
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
    objectUrls.cleanup();
  });
</script>


<div class="content pb-1">
  <h3 class="title is-5 mb-3">Runtime</h3>
  <p>Please be patient with the Install process, it may take a while. Check the console log to confirm success.</p>
  <div class="field has-addons">
    <div class="control">
      <button name="install-runtime" class="button is-warning" title="Install game server"
              disabled={cannotProcess} on:click={installRuntime}>
        <i class="fa fa-gear fa-lg"></i>&nbsp; Install</button>
    </div>
    <div class="control">
      <input class="input" type="text" placeholder="{qualifierName} (optional)"
             title="Optionally specify a {qualifierName.toLowerCase()} to install"
             disabled={cannotProcess} bind:value={qualifier}>
    </div>
  </div>
  <div class="field">
    <div class="control buttons">
      <button name="wipe-runtime" class="button is-danger"
              title="Delete installed game server"
              disabled={cannotProcess} on:click={wipeRuntime}>
        <i class="fa fa-trash-can fa-lg"></i>&nbsp; Delete</button>
      <button name="runtime-meta" class="button is-primary"
              title="View information about the currently installed game server"
              on:click={runtimeMeta}>
        <i class="fa fa-circle-info fa-lg"></i>&nbsp; Meta</button>
    </div>
  </div>
</div>


<style>
  .button {
    width: 130px;
  }
</style>
