<script>
  import { capitalizeKebabCase } from '$lib/util';

  let commands = {
    'world': {
      'broadcast': [
        {input: 'text', type: 'string', name: 'message'}
      ],
      'chopper': []
    },
    'player': {
      'give-xp': [
        {input: 'text', type: 'string', name: 'player', as: 'action'},
        {input: 'radio', type: 'string', name: 'skill', options: ['Aim', 'Carpentry', 'Cooking']},
        {input: 'text', type: 'number', name: 'xp'}
      ],
      'kick': [
        {input: 'text', type: 'string', name: 'player'}
      ],
      'tele-to': []
    },
    'whitelist': {
      'add': [],
      'remove': []
    },
  };

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
	  let url = '/' + command + '/' + action;
	  let data = {};
    commands[command][action].forEach(function(value, index) {
      if (value.type === 'number') {
        data[value.name] = parseInt(args[index]);
      } else {
        data[value.name] = args[index];
      }
    });
	  alert(url + ' ' + JSON.stringify(data));
	}
</script>


<div class="block">
  <div class="field">
    <div class="control">
      {#each Object.keys(commands) as commandOption}
        <label class="radio has-text-weight-bold">
          <input type=radio bind:group={command} name="command" value="{commandOption}">
          {capitalizeKebabCase(commandOption)}
        </label>
      {/each}
    </div>
  </div>
  {#if command}
    <div class="field">
      <div class="control">
        {#each Object.keys(commands[command]) as actionOption}
          <label class="radio has-text-weight-bold">
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
          <div class="field">
            <div class="control">
              {#each arg.options as option}
                <label class="radio has-text-weight-bold">
                  <input type=radio bind:group={args[commands[command][action].indexOf(arg)]} name="{arg.name}" value="{option}"> {capitalizeKebabCase(option)}
                </label>
              {/each}
            </div>
          </div>
        {/if}

      {/each}
      <div class="field">
        <div class="control">
          <button id="send" name="send" class="button is-primary" on:click={send}>Send</button>
        </div>
      </div>
    {/if}
  {/if}
</div>
