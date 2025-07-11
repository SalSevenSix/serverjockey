<script>
  import { getContext } from 'svelte';
  import anchorme from 'anchorme/dist/browser/anchorme.min.js';
  import { hasProp, urlSafeB64encode } from 'common/util/util';
  import { capitalizeKebabCase } from '$lib/util/util';
  import { newGetRequest, newPostRequest } from '$lib/util/sjgmsapi';
  import { notifyInfo, notifyError } from '$lib/util/notifications';
  import InputText from '$lib/widget/InputText.svelte';
  import InputRadio from '$lib/widget/InputRadio.svelte';

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
    if (!current) return;
    commands[command][action].forEach(function(value, index) {
      if (hasProp(value, 'defval')) { args[index] = value.defval; }
    });
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
        text = text.trim().split('\n');
        if (text.length > 1 && text[0] === text[0].toUpperCase()) { text.shift(); }
        text = text.join('\n');
        args[index] = anchorme({ input: text, options: { attributes: { target: '_blank' }}});
      })
      .catch(function() {
        args[index] = ':(';
        notifyError('Failed to load display text for ' + name);
      });
    return '';
  }

  function kpSend(event) {
    if (event.key === 'Enter') {
      send();
      this.select();
    }
  }

  function send() {
    if (cannotSend) return;
    sending = true;
    const body = {};
    let path = '/' + command;
    commands[command][action].forEach(function(value, index) {
      if (!value.type) {
        // Pass
      } else if (value.type === 'item') {
        path += '/' + urlSafeB64encode(args[index]);
      } else if (value.type === 'number') {
        body[value.name] = parseInt(args[index], 10);
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
      .catch(function() { notifyError('Failed to send command to server.'); })
      .finally(function() { sending = false; });
  }
</script>


<div class={Object.keys(commands).length === 1 ? 'is-hidden' : 'content'}>
  <p class="has-text-weight-bold mb-1">Command</p>
  <InputRadio id="commandBuilderCommand" name="command"
              bind:group={command} options={Object.keys(commands)} notranslate />
</div>
{#if command}
  <div class={Object.keys(commands[command]).length === 1 ? 'is-hidden' : 'content'}>
    <p class="has-text-weight-bold mb-1">Action</p>
    <InputRadio id="commandBuilderAction" name="action"
                bind:group={action} options={Object.keys(commands[command])} notranslate />
  </div>
  {#if action}
    <div class="content">
      {#each commands[command][action] as arg}
        {#if arg.input === 'display'}
          {loadDisplay(commands[command][action].indexOf(arg))}
          <pre id="commandBuilderD{arg.name}"
               class="pre is-size-7 notranslate">{@html args[commands[command][action].indexOf(arg)]}</pre>
        {:else if arg.input === 'text' || arg.input === 'text>'}
          <InputText id="commandBuilderI{arg.name}"
                     label={hasProp(arg, 'label') ? arg.label : capitalizeKebabCase(arg.name)}
                     bind:value={args[commands[command][action].indexOf(arg)]}
                     autofocus={arg.input === 'text>'} onKeypress={arg.input === 'text>' ? kpSend : null} />
        {:else if arg.input === 'radio'}
          <p class="has-text-weight-bold mb-1">{capitalizeKebabCase(arg.name)}</p>
          <InputRadio id="commandBuilderR{arg.name}"
                      name={arg.name} options={arg.options} notranslate
                      bind:group={args[commands[command][action].indexOf(arg)]} />
        {/if}
      {/each}
    </div>
    <div class="block buttons">
      <button id="commandBuilderSend" title={sendTitle} class="button is-primary" disabled={cannotSend} on:click={send}>
        <i class="fa fa-paper-plane fa-lg"></i>&nbsp;&nbsp;Send</button>
    </div>
  {/if}
{/if}


<style>
  .button {
    min-width: 10em;
  }
</style>
