<script>
  import { securityToken } from '$lib/serverjockeyapi';
  import Login from '$lib/Login.svelte';
  import ServerLink from '$lib/ServerLink.svelte';
</script>


{#if $securityToken}
  <hr />
  <ServerLink />
  <hr />
{:else}
  <Login />
{/if}
