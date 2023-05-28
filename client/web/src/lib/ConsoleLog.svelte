<script>
  import { onMount, onDestroy, tick } from 'svelte';
  import { notifyError } from '$lib/notifications';
  import { RollingLog } from '$lib/util';
  import { instance, SubscriptionHelper, newGetRequest } from '$lib/sjgmsapi';

  export let hasConsoleLogFile = false;
  let subs = new SubscriptionHelper();
  let logLines = new RollingLog();
  let logText = '';
  let logBox;

  $: if (logText && logBox) {
    tick().then(function() {
      logBox.scroll({ top: logBox.scrollHeight });
    });
  }

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
</script>


<div class="block">
  <div class="field">
    <label for="consoleLogText" class="label">
      {#if hasConsoleLogFile}
        <a href={$instance.url + '/log'} target="_blank">
          Console Log &nbsp;<i class="fa fa-up-right-from-square"></i></a>
      {:else}
        Console Log
      {/if}
    </label>
    <div class="control pr-6">
      <textarea id="consoleLogText" class="textarea is-family-monospace is-size-7"
                bind:this={logBox} readonly>{logText}</textarea>
    </div>
  </div>
</div>
