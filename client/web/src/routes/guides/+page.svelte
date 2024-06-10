<script>
  import { browserName } from '$lib/util/util';
  import { surl } from '$lib/util/sjgmsapi';
  import GuideBooks from '$lib/svg/GuideBooks.svelte';
  import ExtLink from '$lib/widget/ExtLink.svelte';

  const isChrome = browserName === 'Chrome';
  const isEdge = browserName === 'Edge';

  // TODO pull this data from server
  const games = [
    { module: 'projectzomboid', serverName: 'Project Zomboid' },
    { module: 'factorio', serverName: 'Factorio' },
    { module: 'sevendaystodie', serverName: '7 Days to Die' },
    { module: 'starbound', serverName: 'Starbound' },
    { module: 'unturned', serverName: 'Unturned' },
    { module: 'csii', serverName: 'Counter Strike 2' },
    { module: 'palworld', serverName: 'Palworld' }];
</script>


<div class="columns">
  <div class="column is-one-third content mb-0 pb-0">
    <figure class="image max-300"><GuideBooks /></figure>
  </div>
  <div class="column is-two-thirds content">
    <h2 class="title is-3 mt-2">Guides</h2>
    <p>
      If you are reading this, you have successfully installed and started
      <span class="has-text-weight-bold">ServerJockey</span>. Congratulations!
    </p>
    <p>
      The guides section will provide information on how to
      <a href={surl('/guides/discord/setup')}>setup the Discord bot</a>.
      As well as help on how to setup, configure and start supported game servers, and more.
    </p>
  </div>
</div>

<div class="content">
  <hr />
  <h3 class="title is-4">General Guides</h3>
</div>
<div class="columns">
  <div class="column is-one-fifth pb-0 has-text-weight-bold">
    <a href={surl('/guides/discord/setup')}><i class="fa-brands fa-discord fa-lg theme-black-white"></i>
      Discord Bot Setup</a>
  </div>
  <div class="column is-four-fifths content">
    <p>
      This guide will show you how to setup the Discord bot which can be used to manage your servers as an
      alternative to this webapp. The instructions are detailed. If you are unfamiliar with Discord, the guide
      includes instructions on how to register a new Discord account and create a new Discord server if needed.
    </p>
  </div>
</div>
<div class="columns">
  <div class="column is-one-fifth pb-0 has-text-weight-bold">
    <a href={surl('/guides/discord/usage')}><i class="fa-brands fa-discord fa-lg theme-black-white"></i>
      Discord Bot Usage</a>
  </div>
  <div class="column is-four-fifths content">
    <p>
      This guide will show you how to use the Discord bot to create, configure and start
      a Project Zomboid server as an example. The same process can be used on other supported
      game servers too. Please ensure the bot is setup and working first!
    </p>
  </div>
</div>
<div class="columns">
  <div class="column is-one-fifth pb-0 has-text-weight-bold">
    <a href={surl('/guides/extension')}><i class="fa-brands {isEdge ? 'fa-edge' : 'fa-chrome'} fa-lg theme-black-white"></i>
      Browser Extension</a>
  </div>
  <div class="column is-four-fifths content">
    <p>
      ServerJockey has a
      {#if isChrome}
        <ExtLink href="https://chromewebstore.google.com/detail/serverjockey/bcgjnafdidbpegbeijnbpaioipfckiaj"
           >browser extension</ExtLink>
        for Google Chrome
      {:else if isEdge}
        <ExtLink href="https://microsoftedge.microsoft.com/addons/detail/serverjockey/fcfknahceaoeohgehmbialifgdbihloe"
           >browser extension</ExtLink>
        for Microsoft Edge
      {:else}
        browser extension for Google Chrome and Microsoft Edge
      {/if}
      that can be used to manage mods for Project Zomboid servers.
      It allows you to add and remove mods using Steam Workshop pages.
    </p>
  </div>
</div>
<div class="columns">
  <div class="column is-one-fifth pb-0 has-text-weight-bold notranslate">
    <a href={surl('/guides/virtualbox')}><i class="fa fa-computer fa-lg theme-black-white"></i>
      VirtualBox</a>
  </div>
  <div class="column is-four-fifths content">
    <p>
      ServerJockey is available pre-installed as a VirtualBox Appliance. If you are using this option,
      this guide provides information on how to configure, use and care for the appliance.
    </p>
  </div>
</div>
<div class="columns">
  <div class="column is-one-fifth pb-0 has-text-weight-bold">
    <a href={surl('/guides/cli')}><i class="fa fa-terminal fa-lg theme-black-white"></i>
      Command Line Interface</a>
  </div>
  <div class="column is-four-fifths content">
    <p>
      ServerJockey has a Command Line Interface (CLI), which is useful for automating server management.
      This guide will show how to control servers and perform administrative tasks using the CLI.
    </p>
  </div>
</div>
<div class="columns">
  <div class="column is-one-fifth pb-0 has-text-weight-bold">
    <a href={surl('/guides/nginx')}><i class="fa fa-server fa-lg theme-black-white"></i>
      Hosting behind Nginx</a>
  </div>
  <div class="column is-four-fifths content">
    <p>
      Nginx is a popular web server with a powerful reverse proxy feature.
      This guide will show how to combine Nginx and ServerJockey to create a more professional hosting setup.
    </p>
  </div>
</div>
<div class="columns">
  <div class="column is-one-fifth pb-0 has-text-weight-bold">
    <a href={surl('/guides/prometheus')}><i class="fa fa-wave-square fa-lg theme-black-white"></i>
      Monitoring with Prometheus</a>
  </div>
  <div class="column is-four-fifths content">
    <p>
      Prometheus is a flexible and powerful open-source monitoring system that stores metrics in an efficient
      time series database. It can be used to monitor machine health and game servers managed by ServerJockey.
      This guide will show how to install and configure Prometheus.
    </p>
  </div>
</div>

<div class="content">
  <hr />
  <h3 class="title is-4">Game Server Guides</h3>
</div>
<div class="columns is-multiline">
  {#each games as game}
    <div class="column is-one-quarter-desktop is-one-third-tablet">
      <a href={surl('/guides/servers/' + game.module)} title="{game.serverName} guide">
        <div class="card">
          <header class="card-header card-header-title notranslate">{game.serverName}</header>
          <div class="card-image">
            <figure class="image">
              <img src={surl('/assets/games/' + game.module + '-tile.jpg')} alt="{game.serverName} icon" />
            </figure>
          </div>
        </div>
      </a>
    </div>
  {/each}
</div>


<style>
  .fa, .fa-brands {
    width: 26px;
  }

  .card {
    background-color: #F5F5F5;
    color: #485fC7;
    max-width: 400px;
    margin-left: auto;
    margin-right: auto;
  }

  .card:hover {
    color: #363636;
  }

  .card-header-title {
    color: inherit;
  }
</style>
