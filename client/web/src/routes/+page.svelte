<script>
  import { onMount } from 'svelte';
  import { baseurl, newGetRequest } from '$lib/sjgmsapi';
  import SystemInfo from '$lib/SystemInfo.svelte';
  import ServerLink from '$lib/ServerLink.svelte';

  let showServerLink = false;

  onMount(function() {
    fetch(baseurl + '/instances/serverlink', newGetRequest())
      .then(function(response) { showServerLink = response.ok; });
  });
</script>


<SystemInfo />
{#if showServerLink}
  <hr />
  <ServerLink />
{/if}
