<script>
  import { onMount } from 'svelte';
  import { notifyInfo, notifyError } from '$lib/notifications';
  import { instance, newGetRequest, newPostRequest } from '$lib/serverjockeyapi';

  export let noHints = false;
  let serverLinkForm = {};
  let botToken = null;
  let saving = false;

  onMount(function() {
    fetch($instance.url + '/config', newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        serverLinkForm = json;
        botToken = json.BOT_TOKEN;
      })
      .catch(function(error) { notifyError('Failed to load ServerLink Config.'); });
  });

  function save() {
    saving = true;
    let request = newPostRequest('text/plain');
    request.body = JSON.stringify(serverLinkForm);
    fetch($instance.url + '/config', request)
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        botToken = serverLinkForm.BOT_TOKEN;
        notifyInfo('ServerLink Config saved.');
      })
      .catch(function(error) { notifyError('Failed to save ServerLink Config.'); })
      .finally(function() { saving = false; });
  }
</script>


<div class="block">
  {#if !noHints && !botToken}
    <div class="content">
      <p>For help setting up the ServerLink discord bot, please see <a href="/guides/discord">the guide.</a></p>
    </div>
  {/if}
  <div class="field">
    <label for="serverLinkConfigBotToken" class="label">Discord Bot Token</label>
    <div class="control">
      <input id="serverLinkConfigBotToken" class="input" type="text" bind:value={serverLinkForm.BOT_TOKEN}>
    </div>
  </div>
  <div class="field">
    <label for="serverLinkConfigLogChannel" class="label">Log Channel ID</label>
    <div class="control">
      <input id="serverLinkConfigLogChannel" class="input" type="text" bind:value={serverLinkForm.EVENTS_CHANNEL_ID}>
    </div>
  </div>
  <div class="field">
    <label for="serverLinkConfigCommandPrefix" class="label">Command Prefix</label>
    <div class="control">
      <input id="serverLinkConfigCommandPrefix" class="input" type="text" bind:value={serverLinkForm.CMD_PREFIX}>
    </div>
  </div>
  <div class="field">
    <label for="serverLinkConfigAdminRole" class="label">Admin Role</label>
    <div class="control">
      <input id="serverLinkConfigAdminRole" class="input" type="text" bind:value={serverLinkForm.ADMIN_ROLE}>
    </div>
  </div>
  <div class="field">
    <label for="serverLinkConfigWhitelistDm" class="label">Whitelist DM</label>
    <div class="control">
      <textarea id="serverLinkConfigWhitelistDm" class="textarea" bind:value={serverLinkForm.WHITELIST_DM}></textarea>
    </div>
  </div>
  <div class="block buttons">
    <button name="save" title="Save" class="button is-primary is-fullwidth" disabled={saving} on:click={save}>
      <i class="fa fa-floppy-disk fa-lg"></i>&nbsp;&nbsp;Save</button>
  </div>
</div>
