<script>
  import { onMount, onDestroy } from 'svelte';
	import { instance, SubscriptionHelper, newGetRequest } from '$lib/serverjockeyapi';

  let subs = new SubscriptionHelper();
  let logLines = [];
  let logText = '';

	onMount(async function() {
	  let result = await fetch($instance.url + '/log/tail', newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.text();
      })
      .catch(function(error) { alert(error); });
    logLines = result.split('\n');
    logLines.reverse();
    logText = logLines.join('\n');
    await subs.start($instance.url + '/log/subscribe', function(data) {
	    let newLines = data.split('\n');
	    newLines.reverse();
	    logLines = [...newLines, ...logLines];
	    while (logLines.length > 200) { logLines.pop(); }
	    logText = logLines.join('\n');
	    return true;
	  });
	});

	onDestroy(function() {
		subs.stop();
	});

	function openConsoleLog() {
    fetch($instance.url + '/log', newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.blob();
      })
      .then(function(blob) {
        window.open(window.URL.createObjectURL(blob)).focus();
      })
      .catch(function(error) { alert(error); });
  }
</script>


<div class="block">
  <h5 class="title is-5"><a href="#" on:click|preventDefault={openConsoleLog}>Console Log</a></h5>
  <textarea class="textarea" readonly>{logText}</textarea>
</div>
