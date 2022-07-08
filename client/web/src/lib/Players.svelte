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
  <p>Players currently online: {data.length}</p>
  {#each data as player}
    <p>{player.name} ({player.steamid ? player.steamid : 'LOGGING IN'})</p>
  {/each}
</div>
