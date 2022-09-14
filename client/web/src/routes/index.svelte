<script>
  import { securityToken } from '$lib/serverjockeyapi';
  import Login from '$lib/Login.svelte';
  import SystemInfo from '$lib/SystemInfo.svelte';
  import ServerLink from '$lib/ServerLink.svelte';
</script>


{#if $securityToken}
  <SystemInfo />
  <hr />
  <ServerLink />
{:else}
  <Login />
{/if}
<hr />
