<script>
  import { onMount } from 'svelte';
  import { surl, newGetRequest } from '$lib/util/sjgmsapi';

  let hasStore = false;

  onMount(function() {
    fetch(surl('/store'), newGetRequest())
      .then(function(response) { hasStore = response.ok; });
  });
</script>


{#if hasStore}
  <slot />
{/if}
