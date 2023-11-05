<script>
  const games = [
    { module: 'projectzomboid', serverName: 'Project Zomboid', imagePath: '/assets/icons/pz_icon.jpg' },
    { module: 'factorio', serverName: 'Factorio', imagePath: '/assets/icons/ft_icon.jpg' },
    { module: 'sevendaystodie', serverName: '7 Days to Die', imagePath: '/assets/icons/7d2d_icon.jpg' },
    { module: 'starbound', serverName: 'Starbound', imagePath: '/assets/icons/sb_icon.jpg' },
    { module: 'unturned', serverName: 'Unturned', imagePath: '/assets/icons/ut_icon.jpg' },
    { module: 'csii', serverName: 'Counter Strike 2', imagePath: '/assets/icons/csii_icon.jpg' }];
</script>


<div class="columns">
  <div class="column is-one-third content mb-0 pb-0">
    <figure class="image ml-0 mr-0 max-400"><img src="/assets/icons/box.svg" alt="Setup Box" /></figure>
  </div>
  <div class="column is-two-thirds content">
    <h2 class="title is-3 mt-2">Guides</h2>
    <p>
      If you are reading this, you have successfully installed and started
      <span class="has-text-weight-bold">ServerJockey</span>. Congratulations!
    </p>
    <p>
      The guides section will provide information on how to <a href="/guides/discord/setup">setup the Discord bot</a>.
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
    <a href="/guides/discord/setup">Discord Bot Setup</a>
  </div>
  <div class="column is-four-fifths content">
    <p>
      This guide will show you how to setup a Discord bot. You can use the bot on Discord
      to manage your servers as an alternative to this webapp. Most features are supported,
      with a few extra unique features as well.
    </p>
    <p>
      The instructions are detailed. If you are unfamiliar with Discord, the guide also includes instructions
      on where to register a Discord account and how to start a new Discord server (if needed).
    </p>
  </div>
</div>
<div class="columns">
  <div class="column is-one-fifth pb-0 has-text-weight-bold">
    <a href="/guides/discord/usage">Discord Bot Usage</a>
  </div>
  <div class="column is-four-fifths content">
    <p>
      This guide will show you how to use the Discord bot to create, configure and start
      a Project Zomboid server as an example. The same process can be used on other supported
      game servers too. Please make sure the bot is setup and working first!
    </p>
  </div>
</div>
<div class="columns">
  <div class="column is-one-fifth pb-0 has-text-weight-bold">
    <a href="/guides/virtualbox">VirtualBox</a>
  </div>
  <div class="column is-four-fifths content">
    <p>
      ServerJockey is available pre-installed as a VirtualBox Appliance. If you are using this option,
      this guide provides information on how to configure important VirtualBox settings.
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
      <a href="/guides/servers/{game.module}" title="{game.serverName} guide">
        <div class="card">
          <header class="card-header card-header-title">{game.serverName}</header>
          <div class="card-image">
            <figure class="image"><img src="{game.imagePath}" alt="{game.serverName} icon" /></figure>
          </div>
        </div>
      </a>
    </div>
  {/each}
</div>


<style>
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
