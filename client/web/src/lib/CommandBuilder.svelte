<script>
  import { capitalizeKebabCase, stringToBase10 } from '$lib/util';
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
        path += '/' + stringToBase10(args[index]);
      } else if (value.type === 'encoded') {
        body[value.name] = stringToBase10(args[index]);
      } else if (value.type === 'number') {
        body[value.name] = parseInt(args[index]);
      } else {
        body[value.name] = args[index];
      }
    });
    path +=  '/' + action;
    let request = newPostRequest();
    request.body = JSON.stringify(body);
    fetch($instance.url + path, request)
      .then(function(response) { if (!response.ok) throw new Error('Status: ' + response.status); })
      .catch(function(error) { alert('Error ' + error); });
	}
</script>


<div class="content">
  <p class="has-text-weight-bold">Command</p>
  <div class="field">
    <div class="control">
      {#each Object.keys(commands) as commandOption}
        <label class="radio">
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
          <label class="radio">
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
              <input id="{arg.name}" class="input" type="text" bind:value={args[commands[command][action].indexOf(arg)]}>
            </div>
          </div>
        {/if}
        {#if arg.input === 'radio'}
          <p class="has-text-weight-bold">{capitalizeKebabCase(arg.name)}</p>
          <div class="field">
            <div class="control">
              {#each arg.options as option}
                <label class="radio">
                  <input type=radio bind:group={args[commands[command][action].indexOf(arg)]} name="{arg.name}" value="{option}">
                  {capitalizeKebabCase(option)}
                </label>
              {/each}
            </div>
          </div>
        {/if}
      {/each}
      <div class="field">
        <div class="control">
          <button id="send" name="send" class="button is-primary" disabled={!$serverStatus.running} on:click={send}>Send</button>
        </div>
      </div>
    {/if}
  {/if}
</div>
