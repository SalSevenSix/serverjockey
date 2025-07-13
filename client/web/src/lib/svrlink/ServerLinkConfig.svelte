<script>
  import { onMount, getContext } from 'svelte';
  import { notifyInfo, notifyError } from '$lib/util/notifications';
  import { surl, newGetRequest, newPostRequest } from '$lib/util/sjgmsapi';
  import InputPassword from '$lib/widget/InputPassword.svelte';
  import InputText from '$lib/widget/InputText.svelte';
  import InputTextArea from '$lib/widget/InputTextArea.svelte';

  const instance = getContext('instance');

  export let noHints = false;

  let loadedData = normaliseData({});
  let formData = loadedData;
  let processing = true;
  let sectionIndex = 1;

  $: cannotSave = processing || JSON.stringify(loadedData) === JSON.stringify(formData);
  $: showHints = !noHints && !processing && !loadedData.BOT_TOKEN;

  function normaliseData(data) {
    if (!data.EVENT_CHANNELS) { data.EVENT_CHANNELS = {}; }
    if (!data.LLM_API) { data.LLM_API = {}; }
    if (!data.LLM_API.chatbot) { data.LLM_API.chatbot = {}; }
    if (!data.LLM_API.chatbot.messages) { data.LLM_API.chatbot.messages = [{ role: 'system' }]; }
    if (!data.LLM_API.chatlog) { data.LLM_API.chatlog = {}; }
    if (!data.LLM_API.chatlog.messages) { data.LLM_API.chatlog.messages = [{ role: 'system' }, { role: 'user' }]; }
    return data;
  }

  function prevSection() {
    sectionIndex = sectionIndex <= 1 ? 3 : sectionIndex - 1;
  }

  function nextSection() {
    sectionIndex = sectionIndex >= 3 ? 1 : sectionIndex + 1;
  }

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
      .catch(function() { notifyError('Failed to save ServerLink Config.'); })
      .finally(function() { processing = false; });
  }

  onMount(function() {
    fetch(instance.url('/config'), newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        loadedData = normaliseData(json);
        formData = JSON.parse(JSON.stringify(json));
      })
      .catch(function() { notifyError('Failed to load ServerLink Config.'); })
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
  {#if !noHints}
    <div class="block buttons mb-2">
      <button id="serverLinkConfigSectionPrev" title="PREV" class="button is-dark is-small mr-0" on:click={prevSection}>
        <i class="fa fa-circle-chevron-left fa-xl"></i></button>
      <p class="mb-2 ml-3 mr-3">{sectionIndex} / 3</p>
      <button id="serverLinkConfigSectionNext" title="NEXT" class="button is-dark is-small mr-0" on:click={nextSection}>
        <i class="fa fa-circle-chevron-right fa-xl"></i></button>
    </div>
  {/if}
  <div class="block" class:is-hidden={sectionIndex != 1}>
    <InputPassword id="serverLinkConfigDiscordBotToken" label="Discord Bot Token"
       bind:value={formData.BOT_TOKEN} disabled={processing}
       title="Login token for the discord bot" />
    <InputText id="serverLinkConfigCommandPrefix" label="Command Prefix"
       bind:value={formData.CMD_PREFIX} disabled={processing}
       title="Prefix the bot will recognise as commands, more than one character is allowed" />
    <InputText id="serverLinkConfigAdminRoles" label="Admin Roles"
       bind:value={formData.ADMIN_ROLE} disabled={processing}
       title="Discord roles allowed to run admin commands. Multiple roles can be specified using '@' e.g. @PZ Admin @PZ Moderator" />
    <InputText id="serverLinkConfigPlayerRoles" label="Player Roles"
       bind:value={formData.PLAYER_ROLE} disabled={processing}
       title="Discord roles allowed to get server info and use chat integration. Multiple roles can be specified using '@' e.g. @PZ Player @Members" />
    <InputText id="serverLinkConfigServerEventChannelID" label="Server Event Channel ID"
       bind:value={formData.EVENT_CHANNELS.server} disabled={processing}
       title="Discord channel ID for Server events" />
    <InputText id="serverLinkConfigPlayerEventChannelID" label="Player Event Channel ID"
       bind:value={formData.EVENT_CHANNELS.login} disabled={processing}
       title="Discord channel ID for Player login and logout events" />
    <InputText id="serverLinkConfigChatIntegrationChannelID" label="Chat Integration Channel ID"
       bind:value={formData.EVENT_CHANNELS.chat} disabled={processing}
       title="Discord channel ID for Chat integration" />
  </div>
  <div class="block" class:is-hidden={sectionIndex != 2}>
    <InputText id="serverLinkConfigLlmApiBaseurl" label="AI Service URL"
       bind:value={formData.LLM_API.baseurl} disabled={processing}
       placeholder="https://api.deepseek.com" title="OpenAI compatible URL endpoint to use for AI features" />
    <InputPassword id="serverLinkConfigLlmApiToken" label="AI Token"
       bind:value={formData.LLM_API.apikey} disabled={processing}
       title="Login token (api key) for AI service" />
    <InputText id="serverLinkConfigLlmApiChatbotModel" label="AI Chatbot Model"
       bind:value={formData.LLM_API.chatbot.model} disabled={processing}
       placeholder="deepseek-chat" title="Model to use for Chatbot AI feature" />
    {#each formData.LLM_API.chatbot.messages as entry}
      {#if entry && entry.role === 'system'}
        <InputTextArea id="serverLinkConfigLlmApiChatbotSystemPrompt" label="AI Chatbot System Prompt"
           bind:value={entry.content} disabled={processing}
           title="System prompt to use for Chatbot AI feature" />
      {/if}
    {/each}
    <InputText id="serverLinkConfigLlmApiChatlogModel" label="AI Chatlog Model"
       bind:value={formData.LLM_API.chatlog.model} disabled={processing}
       placeholder="deepseek-chat" title="Model to use for Chatlog summary AI feature" />
    {#each formData.LLM_API.chatlog.messages as entry}
      {#if entry && entry.role === 'system'}
        <InputTextArea id="serverLinkConfigLlmApiChatlogSystemPrompt" label="AI Chatlog System Prompt"
           bind:value={entry.content} disabled={processing}
           title="System prompt to use for Chatlog summary AI feature" />
      {:else if entry && entry.role === 'user'}
        <InputTextArea id="serverLinkConfigLlmApiChatlogUserPrompt" label="AI Chatlog User Prompt"
           bind:value={entry.content} disabled={processing}
           title="User prompt to use for Chatlog summary AI feature" />
      {/if}
    {/each}
  </div>
  <div class="block" class:is-hidden={sectionIndex != 3}>
    <InputTextArea id="serverLinkConfigWhitelistDM" label="Whitelist DM"
       bind:value={formData.WHITELIST_DM} disabled={processing}
       title="DM message that will be sent to the user when whitelisted by Discord tag" />
  </div>
  <div class="block buttons">
    <button id="serverLinkConfigSave" title="Save" class="button is-primary is-fullwidth"
            disabled={cannotSave} on:click={save}>
      <i class="fa fa-floppy-disk fa-lg"></i>&nbsp;&nbsp;Save</button>
  </div>
</div>
