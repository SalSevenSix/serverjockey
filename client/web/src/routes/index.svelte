<script>
  import { securityToken } from '$lib/serverjockeyapi';
  import Login from '$lib/Login.svelte';
  import ServerLink from '$lib/ServerLink.svelte';
</script>


<h1>Welcome to ServerJockey</h1>
{#if $securityToken}
  <ServerLink />
{:else}
  <Login />
{/if}

<p>Take me to <a href="/servers">Servers</a></p>
