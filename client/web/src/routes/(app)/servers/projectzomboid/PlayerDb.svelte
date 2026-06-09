<script>
  import { getContext } from 'svelte';
  import { newPostRequest } from '$lib/util/sjgmsapi';
  import { notifyError } from '$lib/util/notifications';
  import InputTextArea from '$lib/widget/InputTextArea.svelte';

  const instance = getContext('instance');
  const serverStatus = getContext('serverStatus');

  let processing = false;
  let outputText = '';
  let inputText = 'SELECT name FROM sqlite_master WHERE type=\'table\';';

  $: cannotExecute = processing || !inputText || $serverStatus.state === 'MAINTENANCE';

  function execute() {
    if (processing) return;
    processing = true;
    const request = newPostRequest('text/plain');
    request.body = inputText;
    fetch(instance.url('/playerdb'), request)
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.text();
      })
      .then(function(text) { outputText = text; })
      .catch(function() { notifyError('Failed to execute SQL'); })
      .finally(function() { processing = false; });
  }
</script>

<div class="content">
  <p>
   <i class="fa fa-triangle-exclamation fa-lg"></i> <span class="has-text-weight-bold">WARNING:</span>&nbsp;
   Updating the database while server is running is not recommended.
  </p>
  <p>
   <i class="fa fa-circle-exclamation fa-lg"></i> <span class="has-text-weight-bold">NOTE:</span>&nbsp;
   It&#39;s recommended that
   <span class="is-family-monospace notranslate">sqlite3</span>
   command line tool is installed on the host machine. This will allow for full
   <span class="notranslate">sqlite3 SQL</span>
   console syntax.
  </p>
</div>
<div class="block">
  <label for="playerDbOutput" class="label" title="Output from SQL executed on the Player DB">Output</label>
  <textarea id="playerDbOutput" class="textarea is-family-monospace is-size-7" style:height="180px"
            disabled={processing} readonly>{outputText}</textarea>
</div>
<div class="block">
  <InputTextArea id="playerDbInput" label="SQL" title="Input SQL (use sqlite3 syntax)"
                 bind:value={inputText} disabled={processing} />
</div>
<div class="block buttons">
  <button id="playerDbExecute" title="Execute SQL on the Player DB" class="button is-primary"
          disabled={cannotExecute} on:click={execute}>
    <i class="fa fa-paper-plane fa-lg"></i>&nbsp;&nbsp;Execute</button>
</div>
