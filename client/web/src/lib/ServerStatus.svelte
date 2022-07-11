<script>
	import { capitalize } from '$lib/util';
	import { serverStatus } from '$lib/serverjockeyapi';
</script>


<div class="block">
  <p>Running: {$serverStatus.running}</p>
  {#if $serverStatus.state}
    <p>State: {$serverStatus.state}</p>
  {/if}
  {#if $serverStatus.details}
    {#each Object.keys($serverStatus.details) as key}
      <p>{capitalize(key)}: {$serverStatus.details[key]}</p>
    {/each}
  {/if}
</div>
