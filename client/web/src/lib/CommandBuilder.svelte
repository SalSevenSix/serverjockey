<script>
  import { notifyInfo, notifyError } from '$lib/notifications';
  import { capitalizeKebabCase, urlSafeB64encode } from '$lib/util';
  import { instance, serverStatus, newPostRequest } from '$lib/serverjockeyapi';

  export let commands;
  let command = null;
  let action = null;
  let args = [null, null, null, null, null, null, null, null, null, null];

  $: resetAction(command);
  function resetAction(c) {
    action = null;
    resetArgs();
  }

  $: resetArgs(action);
  function resetArgs(a) {
    args = [null, null, null, null, null, null, null, null, null, null];
  }

  function send() {
    let path = '/' + command;
    let body = {};
    commands[command][action].forEach(function(value, index) {
      if (value.type === 'item') {
        path += '/' + urlSafeB64encode(args[index]);
      } else if (value.type === 'number') {
        body[value.name] = parseInt(args[index]);
      } else {
        body[value.name] = args[index];
      }
    });
    path += '/' + action;
    let request = newPostRequest();
    request.body = JSON.stringify(body);
    fetch($instance.url + path, request)
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        notifyInfo(capitalizeKebabCase(command) + ' command sent.');
      })
      .catch(function(error) { notifyError('Failed to send command to server.'); });
  }
</script>


<div class="content">
  <p class="has-text-weight-bold">Command</p>
  <div class="field">
    <div class="control">
      {#each Object.keys(commands) as commandOption}
        <label class="radio m-1 p-2">
          <input type=radio bind:group={command} name="command" value="{commandOption}">
          {capitalizeKebabCase(commandOption)}
        </label>
      {/each}
    </div>
  </div>
  {#if command}
    <p class="has-text-weight-bold">Action</p>
    <div class="field">
      <div class="control">
        {#each Object.keys(commands[command]) as actionOption}
          <label class="radio m-1 p-2">
            <input type=radio bind:group={action} name="action" value="{actionOption}">
            {capitalizeKebabCase(actionOption)}
          </label>
        {/each}
      </div>
    </div>
    {#if action}
      {#each commands[command][action] as arg}
        {#if arg.input === 'text'}
          <div class="field">
            <label for="{arg.name}" class="label">{capitalizeKebabCase(arg.name)}</label>
            <div class="control">
              <input id="{arg.name}" class="input" type="text"
                     bind:value={args[commands[command][action].indexOf(arg)]}>
            </div>
          </div>
        {/if}
        {#if arg.input === 'radio'}
          <p class="has-text-weight-bold">{capitalizeKebabCase(arg.name)}</p>
          <div class="field">
            <div class="control">
              {#each arg.options as option}
                <label class="radio m-1 p-2">
                  <input type=radio name="{arg.name}" value="{option}"
                         bind:group={args[commands[command][action].indexOf(arg)]}>
                  {capitalizeKebabCase(option)}
                </label>
              {/each}
            </div>
          </div>
        {/if}
      {/each}
      <div class="field">
        <div class="control">
          <button id="send" name="send" class="button is-primary"
                  disabled={!$serverStatus.running || $serverStatus.state != 'STARTED'}
                  on:click={send}>Send</button>
        </div>
      </div>
    {/if}
  {/if}
</div>


<style>
  .radio {
    background-color: white;
    border: 2px;
    border-style: solid;
    border-color: #dbdbdb;
    border-radius: 5px;
  }
</style>
