<script>
  import { onMount } from 'svelte';

  let stylesheets = $state([]);

  onMount(function() {
    const s = new URLSearchParams(window.location.search).getAll('s');
    if (s && s.length) { stylesheets = [...s]; }
    else { stylesheets = ['styles']; }
  });
</script>


<svelte:head>
  {#each stylesheets as stylesheet}
    <link rel="stylesheet" href="{stylesheet}.css">
  {/each}
</svelte:head>

<slot />
