<script>
  import { securityToken } from '$lib/serverjockeyapi';
  import Login from '$lib/Login.svelte';
  import SystemLoad from '$lib/SystemLoad.svelte';
  import ServerLink from '$lib/ServerLink.svelte';
</script>


{#if $securityToken}
  <SystemLoad />
  <hr />
  <ServerLink />
{:else}
  <Login />
{/if}
