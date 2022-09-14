<script>
  let menuOpen = false;

	function menuToggle() {
	  menuOpen = !menuOpen;
	}

	function menuClose() {
	  menuOpen = false;
	}
</script>


<nav class="navbar is-spaced" aria-label="main navigation">
  <div class="navbar-brand">
    <div class="navbar-item">
      <img src="/assets/rubiks-cube-white.svg" alt="ZomBox" width="28" height="28" />
      <span class="ml-1 is-size-5 has-text-weight-bold">ZomBox</span>
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
      <a on:click={menuClose} class="navbar-item" href="/">Home</a>
      <a on:click={menuClose} class="navbar-item" href="/servers">Instances</a>
      <a on:click={menuClose} class="navbar-item" href="/setup">Setup</a>
      <a on:click={menuClose} class="navbar-item" href="/about">About</a>
    </div>
  </div>
</nav>
<hr />
