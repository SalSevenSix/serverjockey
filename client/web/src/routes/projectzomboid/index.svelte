<script>
  import { instance } from '$lib/serverjockeyapi';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import Players from '$lib/Players.svelte';
</script>


{#if $instance.name}
  <h1>{$instance.name} ({$instance.module})</h1>
  <ServerStatus instance={$instance} />
  <Players instance={$instance} />
{:else}
  <p>No instance set</p>
{/if}
<p><a href="/">BACK</a></p>
