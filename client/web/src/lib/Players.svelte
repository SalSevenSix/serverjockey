<script>
  import { onMount } from 'svelte';
	import { fetchPlayers } from '$lib/serverjockeyapi';

  export let instance;
  let data = [];
	onMount(async function() {
	  data = await fetchPlayers(instance);
	});
</script>


<div>
  <span>Players currently online: {data.length}</span>
  {#each data as player}
    <span>{player.name} ({player.steamid ? player.steamid : 'LOGGING IN'})</span>
  {/each}
</div>
