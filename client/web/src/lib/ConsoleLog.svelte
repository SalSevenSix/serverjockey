<script>
  import { onMount, onDestroy } from 'svelte';
  import { ReverseRollingLog } from '$lib/util';
	import { instance, SubscriptionHelper, newGetRequest, openFileInNewTab } from '$lib/serverjockeyapi';

  let subs = new SubscriptionHelper();
  let logLines = new ReverseRollingLog();
  let logText = '';

	onMount(async function() {
	  let result = await fetch($instance.url + '/log/tail', newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.text();
      })
      .catch(function(error) { alert(error); });
    logText = logLines.set(result).toText();
    await subs.start($instance.url + '/log/subscribe', function(data) {
	    logText = logLines.append(data).toText();
	    return true;
	  });
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
    <label for="console-log" class="label"><a href="javascript:void(0);" on:click|preventDefault={openConsoleLog}>Console Log</a></label>
    <div class="control pr-6">
      <textarea id="console-log" class="textarea" readonly>{logText}</textarea>
    </div>
  </div>
</div>
