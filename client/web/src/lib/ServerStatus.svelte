<script>
  import { onMount } from 'svelte';
	import { capitalize } from '$lib/util';
	import { fetchServerStatus } from '$lib/serverjockeyapi';

  export let instance;
  let data = { running: 'UNKNOWN', state: 'UNKNOWN' };
	onMount(async function() {
	  data = await fetchServerStatus(instance);
	});
</script>


<div>
  <span>Running: {data.running}</span>
  <span>State: {data.state}</span>
  {#if data.details}
    {#each Object.keys(data.details) as key}
      <span>{capitalize(key)}: {data.details[key]}</span>
    {/each}
  {/if}
</div>
