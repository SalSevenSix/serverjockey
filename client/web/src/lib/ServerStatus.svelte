<script>
	import { capitalize } from '$lib/util';
	import { serverStatus } from '$lib/serverjockeyapi';
</script>


<div>
  <p>Running: {$serverStatus.running}</p>
  <p>State: {$serverStatus.state}</p>
  {#if $serverStatus.details}
    {#each Object.keys($serverStatus.details) as key}
      <p>{capitalize(key)}: {$serverStatus.details[key]}</p>
    {/each}
  {/if}
</div>
