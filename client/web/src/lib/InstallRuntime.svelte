<script>
  import { onDestroy } from 'svelte';
  import { notifyInfo, notifyWarning, notifyError } from '$lib/notifications';
  import { confirmModal } from '$lib/modals';
  import { ReverseRollingLog } from '$lib/util';
  import { instance, serverStatus, newPostRequest, SubscriptionHelper, openFileInNewTab } from '$lib/serverjockeyapi';

  export let qualifierName = null;
  export let showLog = false;

  let subs = new SubscriptionHelper();
  let logLines = new ReverseRollingLog();
  let logText = '*** Please wait for Install process to complete before closing section or leaving page ***';
  let qualifier = '';
  let processing = false;

	onDestroy(function() {
		subs.stop();
	});

  function runtimeMeta() {
    openFileInNewTab($instance.url + '/deployment/runtime-meta', function(error) {
      notifyWarning('Meta not found. No runtime installed.');
    });
  }

  function wipeRuntime() {
    confirmModal('Are you sure you want to delete runtime ?', function() {
      processing = true;
      fetch($instance.url + '/deployment/wipe-runtime', newPostRequest())
        .then(function(response) {
          if (!response.ok) throw new Error('Status: ' + response.status);
          notifyInfo('Delete runtime completed.');
        })
        .catch(function(error) { notifyError('Delete runtime failed.'); })
        .finally(function() { processing = false; });
    });
  }

	function installRuntime() {
	  confirmModal(
	    'Are you sure you want to Install Runtime ?\nAny existing install will be overwritten.',
	    doInstallRuntime);
	}

	function doInstallRuntime() {
	  processing = true;
	  logText = logLines.reset().toText();
    let request = newPostRequest();
    let body = { wipe: true, validate: true };
    if (qualifier) { body.beta = qualifier; }
    request.body = JSON.stringify(body);
    fetch($instance.url + '/deployment/install-runtime', request)
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        if (response.status === 204) return null;
        return response.json();
      })
      .then(function(json) {
        if (!json) {
          notifyInfo('Install Runtime completed.');
          processing = false;
        } else if (showLog && json.url) {
          subs.poll(json.url, function(data) {
            logText = logLines.append(data).toText();
            return true;
          })
          .then(function() { notifyInfo('Install Runtime completed. Please check log output for details.'); })
          .finally(function() { processing = false; });
        }
      })
      .catch(function(error) {
        notifyError('Failed to initiate Install Runtime.');
        processing = false;
      });
	}
</script>


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
              disabled={$serverStatus.running || processing} on:click={wipeRuntime}>Delete Runtime</button>
      <button id="install-runtime" name="install-runtime" class="button is-warning"
              disabled={$serverStatus.running || processing} on:click={installRuntime}>Install Runtime</button>
      <button id="runtime-meta" name="runtime-meta" class="button is-primary"
              disabled={$serverStatus.running || processing} on:click={runtimeMeta}>Runtime Meta</button>
    </div>
  </div>
  {#if showLog}
    <div class="field">
      <label for="install-runtime-log" class="label">Install Log</label>
      <div class="control pr-6">
        <textarea id="install-runtime-log" class="textarea is-family-monospace is-size-7" readonly>{logText}</textarea>
      </div>
    </div>
  {:else}
    <p>Please be patient during install. Buttons will be enabled again when complete.</p>
  {/if}
</div>
