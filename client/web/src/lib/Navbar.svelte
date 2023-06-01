<script>
  import { onMount } from 'svelte';
  import RubiksCube from '$lib/RubiksCube.svelte';

  let menuOpen = false;
  let theme = 'light';

  $: themeIcon = theme === 'light' ? 'fa-sun' : 'fa-moon';

  function closeMenu() {
    menuOpen = false;
  }

  function toggleMenu() {
    menuOpen = !menuOpen;
  }

  function setTheme(current) {
    document.body.classList.remove(current === 'light' ? 'dark' : 'light');
    document.body.classList.add(current);
  }

  function toggleTheme() {
    theme = theme === 'light' ? 'dark' : 'light';
    setTheme(theme);
    if (typeof(Storage) !== 'undefined') {
      localStorage.setItem('sjgmsTheme', theme);
    }
    closeMenu();
  }

  onMount(function() {
    if (typeof(Storage) !== 'undefined') {
      let storedTheme = localStorage.getItem('sjgmsTheme');
      theme = storedTheme ? storedTheme : 'light';
    }
    setTheme(theme);
  });
</script>


<div class="block">
  <nav class="navbar is-spaced" aria-label="main navigation">
    <div class="navbar-brand">
      <div class="navbar-item">
        <RubiksCube size="30" />
        <span class="ml-1 is-size-5 has-text-weight-bold">ServerJockey</span>
      </div>
      <a href={'#'} role="button" on:click={toggleMenu} class:is-active={menuOpen}
         class="navbar-burger" aria-label="menu" aria-expanded="false" data-target="navbarMain">
        <span aria-hidden="true"></span>
        <span aria-hidden="true"></span>
        <span aria-hidden="true"></span>
      </a>
    </div>
    <div id="navbarMain" class:is-active={menuOpen} class="navbar-menu">
      <div class="navbar-start">
        <a on:click={closeMenu} class="navbar-item" href="/">
          <i class="fa fa-house fa-lg"></i>&nbsp;&nbsp;Home</a>
        <a on:click={closeMenu} class="navbar-item" href="/servers">
          <i class="fa fa-cubes fa-lg"></i>&nbsp;&nbsp;Instances</a>
        <a on:click={closeMenu} class="navbar-item" href="/guides">
          <i class="fa fa-book fa-lg"></i>&nbsp;&nbsp;Guides</a>
        <a on:click={closeMenu} class="navbar-item" href="/about">
          <i class="fa fa-circle-info fa-lg"></i>&nbsp;&nbsp;About</a>
        <a on:click|preventDefault={toggleTheme} class="navbar-item" href={'#'}>
          &nbsp;<i class="fa {themeIcon} fa-lg"></i>&nbsp;</a>
      </div>
    </div>
  </nav>
</div>
