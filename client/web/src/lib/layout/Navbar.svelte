<script>
  import { surl } from '$lib/util/sjgmsapi';
  import RubiksCube from '$lib/svg/RubiksCube.svelte';
  import FontSizeToggler from '$lib/layout/FontSizeToggler.svelte';
  import ThemeToggler from '$lib/layout/ThemeToggler.svelte';

  let menuOpen = false;

  function closeMenu() {
    menuOpen = false;
  }

  function toggleMenu() {
    menuOpen = !menuOpen;
  }
</script>


<div class="block">
  <nav class="navbar is-spaced" aria-label="main navigation">
    <div class="navbar-brand">
      <div class="navbar-item">
        <RubiksCube size="30" clazz="navbar-rubiks" />
        <span class="ml-1 is-size-5 has-text-weight-bold notranslate">ServerJockey</span>
      </div>
      <a href={'#'} role="button" on:click|preventDefault={toggleMenu} class="navbar-burger"
         class:is-active={menuOpen} aria-label="menu" aria-expanded="false" data-target="navbarMain">
        <span aria-hidden="true"></span>
        <span aria-hidden="true"></span>
        <span aria-hidden="true"></span>
      </a>
    </div>
    <div id="navbarMain" class="navbar-menu" class:is-active={menuOpen}>
      <div class="navbar-start">
        <a id="navbarHome" on:click={closeMenu} class="navbar-item" href={surl('/')}>
          <i class="fa fa-house fa-lg"></i>&nbsp;&nbsp;Home</a>
        <a id="navbarInstances" on:click={closeMenu} class="navbar-item" href={surl('/servers')}>
          <i class="fa fa-cubes fa-lg"></i>&nbsp;&nbsp;Instances</a>
        <a id="navbarGuides" on:click={closeMenu} class="navbar-item" href={surl('/guides')}>
          <i class="fa fa-book fa-lg"></i>&nbsp;&nbsp;Guides</a>
        <a id="navbarAbout" on:click={closeMenu} class="navbar-item" href={surl('/about')}>
          <i class="fa fa-circle-info fa-lg"></i>&nbsp;&nbsp;About</a>
        <FontSizeToggler onAfterToggle={closeMenu} />
        <ThemeToggler onAfterToggle={closeMenu} />
      </div>
    </div>
  </nav>
</div>


<style>
  .navbar-menu.is-active {
    animation: dropmenu .2s ease-in-out;
  }

  @keyframes dropmenu {
    0% {
      display: none;
      opacity: 0;
      height: 0;
    }
    80% {
      display: block;
      opacity: 0;
    }
    100% {
      opacity: 1;
      height: 16em;
    }
  }
</style>
