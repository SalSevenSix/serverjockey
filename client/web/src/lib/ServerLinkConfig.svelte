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
    <label class="label">Discord Token</label>
    <div class="control">
      <input class="input" type="text" bind:value={data.BOT_TOKEN}>
    </div>
  </div>
  <div class="field">
    <label class="label">Log Channel ID</label>
    <div class="control">
      <input class="input" type="text" bind:value={data.EVENTS_CHANNEL_ID}>
    </div>
  </div>
  <div class="field">
    <label class="label">Command Character</label>
    <div class="control">
      <input class="input" type="text" bind:value={data.CMD_PREFIX}>
    </div>
  </div>
  <div class="field">
    <label class="label">Admin Role</label>
    <div class="control">
      <input class="input" type="text" bind:value={data.ADMIN_ROLE}>
    </div>
  </div>
  <div class="field">
    <label class="label">Whitelist DM</label>
    <div class="control">
      <textarea class="textarea" bind:value={data.WHITELIST_DM}></textarea>
    </div>
  </div>
  <div class="field">
    <div class="control">
      <button id="apply" disabled={applying} name="apply" class="button is-primary is-fullwidth" on:click={apply}>Apply</button>
    </div>
  </div>
</div>
