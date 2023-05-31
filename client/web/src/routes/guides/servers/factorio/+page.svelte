<script>
  import { scrollto } from 'svelte-scrollto-element';
  import BackToTop from '$lib/BackToTop.svelte';
</script>


<div class="content">
  <h2 class="title is-3 mt-2">Factorio</h2>
  <p>
    <a href="https://www.factorio.com" target="_blank">Factorio <i class="fa fa-up-right-from-square"></i></a>
    is a factory building game.
  </p>
  <p>
    Jump to <a href="#portForwarding" use:scrollto={'#portForwarding'}>Port Forwarding</a>
  </p>
</div>

<div class="content">
  <hr />
  <h3 class="title is-4">Server setup using the Webapp</h3>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Go to the <a href="/servers" target="_blank">Instances <i class="fa fa-up-right-from-square"></i></a> page.
    If opened in a new tab, you will need to enter the login token again.
  </p>
  <figure><img src="/assets/banners/serverjockey.jpg" alt="Go to instances page" /></figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Create new instance.
  </p>
  <figure><img src="/assets/banners/serverjockey.jpg" alt="Create a new instance" /></figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Go to the new instance.
  </p>
  <figure><img src="/assets/banners/serverjockey.jpg" alt="Go to new instance" /></figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Install runtime. View logging.
  </p>
  <figure><img src="/assets/banners/serverjockey.jpg" alt="Install runtime" /></figure>
  <figure><img src="/assets/banners/serverjockey.jpg" alt="View install logging" /></figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Run server once to generate config. Stop server.
  </p>
  <figure><img src="/assets/banners/serverjockey.jpg" alt="Run server to generate default config" /></figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    View and edit config.
  </p>
  <figure><img src="/assets/banners/serverjockey.jpg" alt="View and edit config" /></figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Wipe game world.
  </p>
  <figure><img src="/assets/banners/serverjockey.jpg" alt="Wipe game world" /></figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Set auto state and startup server again.
  </p>
  <figure><img src="/assets/banners/serverjockey.jpg" alt="Set auto and start server again" /></figure>
</div>

<div class="content" id="additionalInformation">
  <hr />
  <h3 class="title is-4">Additional Information</h3>
</div>

<div class="content" id="portForwarding">
  <h4 class="title is-5">Port Forwarding</h4>
  <p>
    TODO
  </p>
</div>

<BackToTop />
