<script>
  import { onMount, onDestroy } from 'svelte';
  import { notifyError } from '$lib/notifications';
  import { ReverseRollingLog } from '$lib/util';
  import { instance, SubscriptionHelper, newGetRequest, openFileInNewTab } from '$lib/serverjockeyapi';

  export let hasConsoleLogFile = false;
  let subs = new SubscriptionHelper();
  let logLines = new ReverseRollingLog();
  let logText = '';

  onMount(function() {
    fetch($instance.url + '/log/tail', newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.text();
      })
      .then(function(text) {
        logText = logLines.set(text).toText();
        subs.start($instance.url + '/log/subscribe', function(data) {
          logText = logLines.append(data).toText();
          return true;
        });
      })
      .catch(function(error) { notifyError('Failed to load Console Log.'); });
  });

  onDestroy(function() {
    subs.stop();
  });

  function openConsoleLog() {
    openFileInNewTab($instance.url + '/log');
  }
</script>


<div class="block">
  <div class="field">
    <label for="console-log" class="label">
      {#if hasConsoleLogFile}
        <a href={'#'} on:click|preventDefault={openConsoleLog}>Console Log</a>
      {:else}
        Console Log
      {/if}
    </label>
    <div class="control pr-6">
      <textarea id="console-log" class="textarea is-family-monospace is-size-7" readonly>{logText}</textarea>
    </div>
  </div>
</div>
