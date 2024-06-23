<script>
  import { onMount, getContext } from 'svelte';
  import { notifyInfo, notifyError } from '$lib/util/notifications';
  import { surl, newGetRequest, newPostRequest } from '$lib/util/sjgmsapi';
  import InputPassword from '$lib/widget/InputPassword.svelte';
  import InputText from '$lib/widget/InputText.svelte';
  import InputTextArea from '$lib/widget/InputTextArea.svelte';

  const instance = getContext('instance');

  export let noHints = false;

  let loadedData = { 'EVENT_CHANNELS': {} };
  let formData = loadedData;
  let processing = true;

  $: cannotSave = processing || JSON.stringify(loadedData) === JSON.stringify(formData);
  $: showHints = !noHints && !processing && !loadedData.BOT_TOKEN;

  function save() {
    processing = true;
    const request = newPostRequest('text/plain');
    request.body = JSON.stringify(formData);
    fetch(instance.url('/config'), request)
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        loadedData = JSON.parse(JSON.stringify(formData));
        notifyInfo('ServerLink Config saved.');
      })
      .catch(function(error) { notifyError('Failed to save ServerLink Config.'); })
      .finally(function() { processing = false; });
  }

  onMount(function() {
    fetch(instance.url('/config'), newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        loadedData = json;
        formData = JSON.parse(JSON.stringify(json));
      })
      .catch(function(error) { notifyError('Failed to load ServerLink Config.'); })
      .finally(function() { processing = false; });
  });
</script>


<div class="block">
  {#if showHints}
    <div class="content">
      <p>For help setting up the ServerLink discord bot, please see
         <a href={surl('/guides/discord/setup')}>the guide</a>.</p>
    </div>
  {/if}
  <InputPassword id="serverLinkConfigBotToken" name="Discord Bot Token"
     bind:value={formData.BOT_TOKEN} disabled={processing}
     title="Login token for the discord bot" />
  <InputText id="serverLinkConfigCommandPrefix" name="Command Prefix"
     bind:value={formData.CMD_PREFIX} disabled={processing}
     title="Prefix the bot will recognise as commands, more than one character is allowed" />
  <InputText id="serverLinkConfigAdminRole" name="Admin Roles"
     bind:value={formData.ADMIN_ROLE} disabled={processing}
     title="Discord roles allowed to run admin commands. Multiple roles can be specified using '@' e.g. @PZ Admin @PZ Moderator" />
  <InputText id="serverLinkConfigPlayerRole" name="Player Roles"
     bind:value={formData.PLAYER_ROLE} disabled={processing}
     title="Discord roles allowed to get server info and use chat integration. Multiple roles can be specified using '@' e.g. @PZ Player @Members" />
  <InputText id="serverLinkConfigChannelEventsServer" name="Server Event Channel ID"
     bind:value={formData.EVENT_CHANNELS.server} disabled={processing}
     title="Discord channel ID for Server events" />
  <InputText id="serverLinkConfigChannelEventsPlayerLogin" name="Player Event Channel ID"
     bind:value={formData.EVENT_CHANNELS.login} disabled={processing}
     title="Discord channel ID for Player login and logout events" />
  <InputText id="serverLinkConfigChannelEventsPlayerChat" name="Chat Integration Channel ID"
     bind:value={formData.EVENT_CHANNELS.chat} disabled={processing}
     title="Discord channel ID for Chat integration" />
  <InputTextArea id="serverLinkConfigWhitelistDm" name="Whitelist DM"
     bind:value={formData.WHITELIST_DM} disabled={processing}
     title="DM message that will be sent to the user when whitelisted by Discord tag" />
  <div class="block buttons">
    <button name="save" title="Save" class="button is-primary is-fullwidth"
            disabled={cannotSave} on:click={save}>
      <i class="fa fa-floppy-disk fa-lg"></i>&nbsp;&nbsp;Save</button>
  </div>
</div>
