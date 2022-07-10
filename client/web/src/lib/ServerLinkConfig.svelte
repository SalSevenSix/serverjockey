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

<div>
  <p>Token <input style="width: 66%" bind:value={data.BOT_TOKEN} /></p>
  <p>Channel ID <input style="width: 66%" bind:value={data.EVENTS_CHANNEL_ID} /></p>
  <p>Command Character <input style="width: 33%" bind:value={data.CMD_PREFIX} /></p>
  <p>Admin Role <input style="width: 33%" bind:value={data.ADMIN_ROLE} /></p>
  <p>Whitelist DM <input style="width: 80%" bind:value={data.WHITELIST_DM} /></p>
  <button id="apply" disabled={applying} name="apply" on:click={apply}>Apply</button>
</div>
