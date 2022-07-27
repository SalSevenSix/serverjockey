<script>
  import { onDestroy } from 'svelte';
  import { ReverseRollingLog } from '$lib/util';
  import { instance, serverStatus, newPostRequest, SubscriptionHelper } from '$lib/serverjockeyapi';

  export let qualifierName = 'Qualifier';
  export let showLog = false;

  let subs = new SubscriptionHelper();
  let logLines = new ReverseRollingLog();
  let logText = '';
  let qualifier = '';
  let installing = false;

	onDestroy(function() {
		subs.stop();
	});

  function installDone() {
    installing = false;
  }

	function install() {
	  if (!confirm('Are you sure you want to Install Runtime ?')) return;
	  installing = true;
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
          installDone();  // Assuming 204 means it blocked until done
        } else if (showLog && json.url) {
          subs.poll(json.url, function(data) {
            logText = logLines.append(data).toText();
            return true;
          })
          .finally(installDone);
        }
      })
      .catch(function(error) {
        alert('Error ' + error);
        installDone();
      });
	}
</script>


<div class="block">
  <div class="field">
    <label for="install-runtime-qualifier" class="label">{qualifierName}</label>
    <div class="control">
      <input id="install-runtime-qualifier" class="input" type="text" bind:value={qualifier}>
    </div>
  </div>
  <div class="field">
    <div class="control">
      <button id="install-runtime" disabled={$serverStatus.running || installing} name="install" class="button is-primary" on:click={install}>Install Runtime</button>
    </div>
  </div>
  {#if showLog}
    <div class="field">
      <label for="install-runtime-log" class="label">Install Log</label>
      <div class="control pr-6">
        <textarea id="install-runtime-log" class="textarea" readonly>{logText}</textarea>
      </div>
    </div>
  {/if}
</div>
