<script>
  import { onMount } from 'svelte';
  import { notifyInfo, notifyError } from '$lib/notifications';
  import { instance, newGetRequest, newPostRequest } from '$lib/serverjockeyapi';

  let serverLinkForm = {};
  let applying = false;

  onMount(function() {
    fetch($instance.url + '/config', newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) { serverLinkForm = json; })
      .catch(function(error) { notifyError('Failed to load ServerLink Config.'); });
  });

  function apply() {
    applying = true;
    let request = newPostRequest('text/plain');
    request.body = JSON.stringify(serverLinkForm);
    fetch($instance.url + '/config', request)
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        notifyInfo('ServerLink Config saved.');
      })
      .catch(function(error) { notifyError('Failed to save ServerLink Config.'); })
      .finally(function() { applying = false; });
  }
</script>


<div class="block">
  <div class="field">
    <label for="bot-token" class="label">Discord Bot Token</label>
    <div class="control">
      <input id="bot-token" class="input" type="text" bind:value={serverLinkForm.BOT_TOKEN}>
    </div>
  </div>
  <div class="field">
    <label for="log-channel" class="label">Log Channel ID</label>
    <div class="control">
      <input id="log-channel" class="input" type="text" bind:value={serverLinkForm.EVENTS_CHANNEL_ID}>
    </div>
  </div>
  <div class="field">
    <label for="command-prefix" class="label">Command Prefix</label>
    <div class="control">
      <input id="command-prefix" class="input" type="text" bind:value={serverLinkForm.CMD_PREFIX}>
    </div>
  </div>
  <div class="field">
    <label for="admin-role" class="label">Admin Role</label>
    <div class="control">
      <input id="admin-role" class="input" type="text" bind:value={serverLinkForm.ADMIN_ROLE}>
    </div>
  </div>
  <div class="field">
    <label for="whitelist-dm" class="label">Whitelist DM</label>
    <div class="control">
      <textarea id="whitelist-dm" class="textarea" bind:value={serverLinkForm.WHITELIST_DM}></textarea>
    </div>
  </div>
  <div class="field">
    <div class="control">
      <button id="apply" disabled={applying} name="apply" class="button is-primary is-fullwidth" on:click={apply}>
        Apply</button>
    </div>
  </div>
</div>
