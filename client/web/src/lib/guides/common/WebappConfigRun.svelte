<script>
  import { surl } from '$lib/util/sjgmsapi';
</script>


<div class="content">
  <p><span class="step-title"></span>
    With the game server fully installed now, you can view and edit the configuration files. Expand the
    <span class="has-text-weight-bold">Configuration</span> section. Edit and save the configuration as desired.
    Make sure changes are saved before closing the section, otherwise the changes will be lost!
  </p>
  <figure class="image max-600 is-bordered">
    <img src={surl('/assets/guides/games/configuration.png')} alt="View and edit config" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    With installation and configuration complete, your game server is ready to use.
    You can optionally set the <span class="has-text-weight-bold">Auto</span> behaviour.
  </p>
  <table class="table is-thinner">
    <tbody>
      <tr><td class="has-text-weight-bold">Off</td>
          <td>No automatic actions</td></tr>
      <tr><td class="has-text-weight-bold">Start</td>
          <td>Automatically start the game server when ServerJockey starts</td></tr>
      <tr><td class="has-text-weight-bold">Restart</td>
          <td>Automatically restart the game server if it crashes</td></tr>
      <tr><td class="has-text-weight-bold">Start and Restart</td>
          <td>Both automatic Start and Restart actions</td></tr>
    </tbody>
  </table>
  <p>
    Use the Start, Stop and Restart buttons to control your server as needed.
  </p>
  <div class="columns is-gapless">
    <div class="column">
      <figure class="image max-400 is-bordered mb-2">
        <img src={surl('/assets/guides/games/set_auto.png')} alt="Set auto setting" loading="lazy" />
      </figure>
    </div>
    <div class="column">
      <figure class="image max-400 is-bordered mb-2">
        <img src={surl('/assets/guides/games/server_start.png')} alt="Start server" loading="lazy" />
      </figure>
    </div>
  </div>
</div>
