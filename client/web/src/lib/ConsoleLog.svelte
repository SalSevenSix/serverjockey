<script>
  import { onMount, onDestroy } from 'svelte';
	import { instance, subscribeAndPoll } from '$lib/serverjockeyapi';

  let polling = true;
  let logLines = [];
  let logText = '';
	onMount(async function() {
	  let result = await fetch($instance.url + '/log/tail')
      .then(function(response) { return response.text(); })
      .catch(function(error) { alert(error); });
    logLines = result.split('\n');
    logLines.reverse();
    logText = logLines.join('\n');
    subscribeAndPoll($instance.url + '/log/subscribe', function(data) {
	    if (data == null || !polling) return polling;
	    let newLines = data.split('\n');
	    newLines.reverse();
	    logLines = [...newLines, ...logLines];
	    while (logLines.length > 200) { logLines.pop(); }
	    logText = logLines.join('\n');
	    return polling;
	  });
	});

	onDestroy(function() {
	  polling = false;
	});
</script>


<div class="column">
  <textarea class="textarea" readonly>{logText}</textarea>
</div>
