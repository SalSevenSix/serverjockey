<script>
  import { onMount } from 'svelte';
  import { noStorage } from '$lib/util/util';

  export let clazz = '';
  export let onAfterToggle = function() {};

  let themeLink;
  let theme = 'light';

  $: themeIcon = theme === 'light' ? 'fa-sun' : 'fa-moon';

  function setTheme(current) {
    if (!document) return;
    if (!document.body) return;
    document.body.classList.remove(current === 'light' ? 'dark' : 'light');
    document.body.classList.add(current);
    if (!document.body.parentElement) return;
    document.body.parentElement.classList.remove(current === 'light' ? 'dark' : 'light');
    document.body.parentElement.classList.add(current);
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


<a bind:this={themeLink} href={'#'} class={clazz}
   on:click|preventDefault={toggleTheme}>&nbsp;<i class="fa {themeIcon} fa-lg"></i>&nbsp;</a>
