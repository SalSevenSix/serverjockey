<script>
  import { onMount } from 'svelte';
  import RubiksCube from '$lib/RubiksCube.svelte';

  let menuOpen = false;
  let darkMode = true;

  function menuToggle() {
    menuOpen = !menuOpen;
  }

  function menuClose() {
    menuOpen = false;
  }

  function darkModeToggle() {
    if (darkMode) {
      document.body.classList.remove('dark');
      document.body.classList.add('light');
    } else {
      document.body.classList.remove('light');
      document.body.classList.add('dark');
    }
    darkMode = !darkMode;
    if (typeof(Storage) !== 'undefined') {
      localStorage.setItem('sjgmsDarkMode', darkMode);
    }
    menuClose();
  }

  onMount(function() {
    if (typeof(Storage) !== 'undefined') {
      darkMode = localStorage.getItem('sjgmsDarkMode') ? false : true;
    }
    darkModeToggle();
  });
</script>


<div class="block">
  <nav class="navbar is-spaced" aria-label="main navigation">
    <div class="navbar-brand">
      <div class="navbar-item">
        <RubiksCube size="30" />
        <span class="ml-1 is-size-5 has-text-weight-bold">ServerJockey</span>
      </div>
      <a href={'#'} role="button" on:click={menuToggle} class:is-active={menuOpen}
         class="navbar-burger" aria-label="menu" aria-expanded="false" data-target="navbarMain">
        <span aria-hidden="true"></span>
        <span aria-hidden="true"></span>
        <span aria-hidden="true"></span>
      </a>
    </div>
    <div id="navbarMain" class:is-active={menuOpen} class="navbar-menu">
      <div class="navbar-start">
        <a on:click={menuClose} class="navbar-item" href="/">
          <i class="fa fa-house fa-lg"></i>&nbsp;&nbsp;Home</a>
        <a on:click={menuClose} class="navbar-item" href="/servers">
          <i class="fa fa-cubes fa-lg"></i>&nbsp;&nbsp;Instances</a>
        <a on:click={menuClose} class="navbar-item" href="/guides">
          <i class="fa fa-book fa-lg"></i>&nbsp;&nbsp;Guides</a>
        <a on:click={menuClose} class="navbar-item" href="/about">
          <i class="fa fa-circle-info fa-lg"></i>&nbsp;&nbsp;About</a>
        <a on:click|preventDefault={darkModeToggle} class="navbar-item" href={'#'}>
          &nbsp;<i class="fa fa-{darkMode ? 'moon' : 'sun'} fa-lg"></i>&nbsp;</a>
      </div>
    </div>
  </nav>
</div>
