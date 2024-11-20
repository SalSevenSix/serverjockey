<script>
  import { surl } from '$lib/util/sjgmsapi';

  const games = [
    { module: 'projectzomboid', serverName: 'Project Zomboid' },
    { module: 'factorio', serverName: 'Factorio' },
    { module: 'sevendaystodie', serverName: '7 Days to Die' },
    { module: 'starbound', serverName: 'Starbound' },
    { module: 'unturned', serverName: 'Unturned' },
    { module: 'csii', serverName: 'Counter Strike 2' },
    { module: 'palworld', serverName: 'Palworld' }];
</script>


<div class="columns is-multiline">
  {#each games as game}
    <div class="column is-one-quarter-desktop is-one-third-tablet">
      <a id="gameServerGuidesM{game.module}" title="{game.serverName} guide"
         href={surl('/guides/servers/' + game.module)}>
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
  .card {
    background-color: #F5F5F5;
    color: #485fC7;
    max-width: 400px;
    margin-left: auto;
    margin-right: auto;
  }

  .card:hover {
    color: var(--color-standard-darker-bwg);
  }

  .card-header-title {
    color: inherit;
  }
</style>
