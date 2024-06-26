<script>
  import { getContext } from 'svelte';
  import anchorme from 'anchorme/dist/browser/anchorme.min.js';
  import { notifyInfo, notifyError } from '$lib/util/notifications';
  import { capitalizeKebabCase, urlSafeB64encode } from '$lib/util/util';
  import { newGetRequest, newPostRequest } from '$lib/util/sjgmsapi';

  const instance = getContext('instance');
  const serverStatus = getContext('serverStatus');

  export let commands;

  let args = [null, null, null, null, null, null, null, null, null, null];
  let action = null;
  let command = Object.keys(commands).length === 1 ? Object.keys(commands)[0] : null;
  let sending = false;

  $: commandUpdated(command); function commandUpdated(current) {
    action = current && Object.keys(commands[current]).length === 1 ? Object.keys(commands[current])[0] : null;
  }

  $: actionUpdated(action); function actionUpdated(current) {
    args = [null, null, null, null, null, null, null, null, null, null];
  }

  $: cannotSend = sending || !($serverStatus.state === 'STARTED');
  $: sendTitle = cannotSend ? 'Cannot send commands, server not STARTED' : 'Send command';

  function loadDisplay(index) {
    args[index] = 'loading...\n\n\n';
    const name = commands[command][action][index].name;
    fetch(instance.url('/' + command + '/' + name), newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.text();
      })
      .then(function(text) {
        args[index] = anchorme({ input: text, options: { attributes: { target: '_blank' }}});
      })
      .catch(function(error) {
        args[index] = ':(';
        notifyError('Failed to load display text for ' + name);
      });
    return '';
  }

  function kpSend(event) {
    if (event.key === 'Enter') { send(); }
  }

  function send() {
    if (cannotSend) return;
    sending = true;
    const body = {};
    let path = '/' + command;
    commands[command][action].forEach(function(value, index) {
      if (!value.type) {
        // pass
      } else if (value.type === 'item') {
        path += '/' + urlSafeB64encode(args[index]);
      } else if (value.type === 'number') {
        body[value.name] = parseInt(args[index]);
      } else {
        body[value.name] = args[index];
      }
    });
    path += '/' + action;
    const request = newPostRequest();
    request.body = JSON.stringify(body);
    fetch(instance.url(path), request)
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        notifyInfo(capitalizeKebabCase(command) + ' command sent.');
      })
      .catch(function(error) { notifyError('Failed to send command to server.'); })
      .finally(function() { sending = false; });
  }
</script>


<div class={Object.keys(commands).length === 1 ? 'is-hidden' : 'content'}>
  <p class="has-text-weight-bold">Command</p>
  <div class="field">
    <div class="control">
      {#each Object.keys(commands) as commandOption}
        <label class="radio m-1 p-2 notranslate">
          <input type="radio" bind:group={command} name="command" value={commandOption}>
          {capitalizeKebabCase(commandOption)}
        </label>
      {/each}
    </div>
  </div>
</div>
{#if command}
  <div class={Object.keys(commands[command]).length === 1 ? 'is-hidden' : 'content'}>
    <p class="has-text-weight-bold">Action</p>
    <div class="field">
      <div class="control">
        {#each Object.keys(commands[command]) as actionOption}
          <label class="radio m-1 p-2 notranslate">
            <input type="radio" bind:group={action} name="action" value={actionOption}>
            {capitalizeKebabCase(actionOption)}
          </label>
        {/each}
      </div>
    </div>
  </div>
  {#if action}
    <div class="content">
      {#each commands[command][action] as arg}
        {#if arg.input === 'display'}
          {loadDisplay(commands[command][action].indexOf(arg))}
          <p class="has-text-weight-bold">{capitalizeKebabCase(arg.name)}</p>
          <pre class="pre is-size-7 notranslate">{@html args[commands[command][action].indexOf(arg)]}</pre>
        {/if}
        {#if arg.input === 'text' || arg.input === 'text>'}
          <div class="field">
            <label for="commandBuilderI{arg.name}" class="label">{capitalizeKebabCase(arg.name)}</label>
            <div class="control">
              {#if arg.input === 'text'}
                <input id="commandBuilderI{arg.name}" class="input" type="text"
                       bind:value={args[commands[command][action].indexOf(arg)]}>
              {:else}
                <!-- svelte-ignore a11y-autofocus -->
                <input autofocus on:keypress={kpSend}
                       id="commandBuilderI{arg.name}" class="input" type="text"
                       bind:value={args[commands[command][action].indexOf(arg)]}>
              {/if}
            </div>
          </div>
        {/if}
        {#if arg.input === 'radio'}
          <p class="has-text-weight-bold">{capitalizeKebabCase(arg.name)}</p>
          <div class="field">
            <div class="control">
              {#each arg.options as option}
                <label class="radio m-1 p-2 notranslate">
                  <input type="radio" name={arg.name} value={option}
                         bind:group={args[commands[command][action].indexOf(arg)]}>
                  {capitalizeKebabCase(option)}
                </label>
              {/each}
            </div>
          </div>
        {/if}
      {/each}
    </div>
    <div class="block buttons">
      <button name="send" title={sendTitle} class="button is-primary" disabled={cannotSend} on:click={send}>
        <i class="fa fa-paper-plane fa-lg"></i>&nbsp;&nbsp;Send</button>
    </div>
  {/if}
{/if}


<style>
  .radio {
    background-color: white;
    border: 2px;
    border-style: solid;
    border-color: #DBDBDB;
    border-radius: 5px;
  }
</style>
