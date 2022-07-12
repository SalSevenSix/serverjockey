<script>
  import { securityToken } from '$lib/serverjockeyapi';
  import Login from '$lib/Login.svelte';
  import ServerLink from '$lib/ServerLink.svelte';
</script>


{#if $securityToken}
  <ServerLink />
{:else}
  <Login />
{/if}
