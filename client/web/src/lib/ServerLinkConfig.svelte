<script>
  import { onMount } from 'svelte';
  import { notifyInfo, notifyError } from '$lib/notifications';
  import { newGetRequest, newPostRequest } from '$lib/sjgmsapi';
  import { instance } from '$lib/instancestores';

  export let noHints = false;

  let serverLinkForm = { 'EVENT_CHANNELS': {} };
  let botToken = null;
  let processing = true;

  function save() {
    processing = true;
    let request = newPostRequest('text/plain');
    request.body = JSON.stringify(serverLinkForm);
    fetch($instance.url + '/config', request)
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        botToken = serverLinkForm.BOT_TOKEN;
        notifyInfo('ServerLink Config saved.');
      })
      .catch(function(error) { notifyError('Failed to save ServerLink Config.'); })
      .finally(function() { processing = false; });
  }

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
      .catch(function(error) { notifyError('Failed to load ServerLink Config.'); })
      .finally(function() { processing = false; });
  });
</script>


<div class="block">
  {#if !noHints && !botToken}
    <div class="content">
      <p>For help setting up the ServerLink discord bot, please see <a href="/guides/discord/setup">the guide</a>.</p>
    </div>
  {/if}
  <div class="field">
    <label for="serverLinkConfigBotToken" class="label"
           title="Login token for the discord bot">
      Discord Bot Token</label>
    <div class="control">
      <input id="serverLinkConfigBotToken" class="input" type="text"
             disabled={processing} bind:value={serverLinkForm.BOT_TOKEN}>
    </div>
  </div>
  <div class="field">
    <label for="serverLinkConfigCommandPrefix" class="label"
           title="Prefix the bot will recognise as commands, more than one character is allowed">
      Command Prefix</label>
    <div class="control">
      <input id="serverLinkConfigCommandPrefix" class="input" type="text"
             disabled={processing} bind:value={serverLinkForm.CMD_PREFIX}>
    </div>
  </div>
  <div class="field">
    <label for="serverLinkConfigAdminRole" class="label"
           title="Discord roles allowed to run admin commands. Multiple roles can be specified using '@' e.g. @PZ Admin @PZ Moderator">
      Admin Roles</label>
    <div class="control">
      <input id="serverLinkConfigAdminRole" class="input" type="text"
             disabled={processing} bind:value={serverLinkForm.ADMIN_ROLE}>
    </div>
  </div>
  <div class="field">
    <label for="serverLinkConfigPlayerRole" class="label"
           title="Discord roles allowed to get server info and use chat integration. Multiple roles can be specified using '@' e.g. @PZ Player @Members">
      Player Roles</label>
    <div class="control">
      <input id="serverLinkConfigPlayerRole" class="input" type="text"
             disabled={processing} bind:value={serverLinkForm.PLAYER_ROLE}>
    </div>
  </div>
  <div class="field">
    <label for="serverLinkConfigChannelEventsServer" class="label"
           title="Discord channel ID for Server event logging">
      Server Event Channel ID</label>
    <div class="control">
      <input id="serverLinkConfigChannelEventsServer" class="input" type="text"
             disabled={processing} bind:value={serverLinkForm.EVENT_CHANNELS.server}>
    </div>
  </div>
  <div class="field">
    <label for="serverLinkConfigChannelEventsPlayerLogin" class="label"
           title="Discord channel ID for Player login/logout event logging">
      Player Event Channel ID</label>
    <div class="control">
      <input id="serverLinkConfigChannelEventsPlayerLogin" class="input" type="text"
             disabled={processing} bind:value={serverLinkForm.EVENT_CHANNELS.login}>
    </div>
  </div>
  <div class="field">
    <label for="serverLinkConfigChannelEventsPlayerChat" class="label"
           title="Discord channel ID for Chat integration">
      Chat Integration Channel ID</label>
    <div class="control">
      <input id="serverLinkConfigChannelEventsPlayerChat" class="input" type="text"
             disabled={processing} bind:value={serverLinkForm.EVENT_CHANNELS.chat}>
    </div>
  </div>
  <div class="field">
    <label for="serverLinkConfigWhitelistDm" class="label"
           title="DM message that will be sent to the user when whitelisted by Discord tag">
      Whitelist DM</label>
    <div class="control">
      <textarea id="serverLinkConfigWhitelistDm" class="textarea"
                disabled={processing} bind:value={serverLinkForm.WHITELIST_DM}></textarea>
    </div>
  </div>
  <div class="block buttons">
    <button name="save" title="Save" class="button is-primary is-fullwidth" disabled={processing} on:click={save}>
      <i class="fa fa-floppy-disk fa-lg"></i>&nbsp;&nbsp;Save</button>
  </div>
</div>
