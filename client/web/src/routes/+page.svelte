<script>
  import { onMount } from 'svelte';
  import { newGetRequest } from '$lib/sjgmsapi';
  import SystemInfo from '$lib/SystemInfo.svelte';
  import ServerLink from '$lib/ServerLink.svelte';
  import SystemLog from '$lib/SystemLog.svelte';

  let showServerLink = false;

  onMount(function() {
    fetch('/instances/serverlink', newGetRequest())
      .then(function(response) { showServerLink = response.ok; });
  });
</script>


<SystemInfo />
{#if showServerLink}
  <hr />
  <ServerLink />
{/if}
<SystemLog />
