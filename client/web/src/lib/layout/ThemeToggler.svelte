<script>
  import { onMount } from 'svelte';
  import { fNoop, noStorage } from '$lib/util/util';

  export let onAfterToggle = fNoop;

  let themeLink;
  let theme = 'light';

  $: themeIcon = theme === 'light' ? 'fa-sun' : 'fa-moon';

  function setTheme(current) {
    if (!document) return;
    if (!document.body) return;
    document.body.classList.remove(current === 'light' ? 'dark' : 'light');
    document.body.classList.add(current);
    if (!document.documentElement) return;
    document.documentElement.classList.remove(current === 'light' ? 'dark' : 'light');
    document.documentElement.classList.add(current);
  }

  function toggleTheme() {
    if (themeLink.blur) { themeLink.blur(); }
    theme = theme === 'light' ? 'dark' : 'light';
    setTheme(theme);
    if (!noStorage) {
      localStorage.setItem('sjgmsTheme', theme);
    }
    onAfterToggle();
  }

  onMount(function() {
    if (!noStorage) {
      const storedTheme = localStorage.getItem('sjgmsTheme');
      theme = storedTheme ? storedTheme : 'light';
    }
    setTheme(theme);
  });
</script>


<a id="navbarTheme" bind:this={themeLink} href={'#'} class="navbar-item"
   on:click|preventDefault={toggleTheme}>&nbsp;<i class="fa {themeIcon} fa-lg"></i>&nbsp;</a>
