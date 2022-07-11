<script>
  import { securityToken } from '$lib/serverjockeyapi';
  import Login from '$lib/Login.svelte';
  import ServerLink from '$lib/ServerLink.svelte';
</script>


<div>
  {#if $securityToken}
    <ServerLink />
  {:else}
    <Login />
  {/if}
  <div class="block">
    <p>Take me to <a href="/servers">Servers</a></p>
  </div>
</div>
