<script>
  import { onMount } from 'svelte';
  import { instance, fetchJson, postText } from '$lib/serverjockeyapi';

  let data = {};
	onMount(async function() {
    data = await fetchJson($instance.url + '/config');
	});

  let applying = false;
	function apply() {
	  applying = true;
	  postText($instance.url + '/config', JSON.stringify(data), function() {
	    applying = false;
	  });
	}
</script>


<div class="block">
  <div class="field">
    <label for="bot-token" class="label">Discord Bot Token</label>
    <div class="control">
      <input id="bot-token" class="input" type="text" bind:value={data.BOT_TOKEN}>
    </div>
  </div>
  <div class="field">
    <label for="log-channel" class="label">Log Channel ID</label>
    <div class="control">
      <input id="log-channel" class="input" type="text" bind:value={data.EVENTS_CHANNEL_ID}>
    </div>
  </div>
  <div class="field">
    <label for="command-character" class="label">Command Character</label>
    <div class="control">
      <input id="command-character" class="input" type="text" bind:value={data.CMD_PREFIX}>
    </div>
  </div>
  <div class="field">
    <label for="admin-role" class="label">Admin Role</label>
    <div class="control">
      <input id="admin-role" class="input" type="text" bind:value={data.ADMIN_ROLE}>
    </div>
  </div>
  <div class="field">
    <label for="whitelist-dm" class="label">Whitelist DM</label>
    <div class="control">
      <textarea id="whitelist-dm" class="textarea" bind:value={data.WHITELIST_DM}></textarea>
    </div>
  </div>
  <div class="field">
    <div class="control">
      <button id="apply" disabled={applying} name="apply" class="button is-primary is-fullwidth" on:click={apply}>Apply</button>
    </div>
  </div>
</div>
