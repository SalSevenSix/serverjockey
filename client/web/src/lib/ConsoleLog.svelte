<script>
  import { onMount, onDestroy } from 'svelte';
	import { instance, SubscriptionHelper } from '$lib/serverjockeyapi';

  let subs = new SubscriptionHelper();
  let logLines = [];
  let logText = '';

	onMount(async function() {
	  let result = await fetch($instance.url + '/log/tail')
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
</script>


<div class="column">
  <textarea class="textarea" readonly>{logText}</textarea>
</div>
