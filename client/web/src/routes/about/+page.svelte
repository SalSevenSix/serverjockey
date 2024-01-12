<script>
  import RubiksCube from '$lib/widget/RubiksCube.svelte';
</script>


<div class="columns">
  <div class="column is-one-third content mb-0">
    <figure class="image max-400"><RubiksCube dazzle /></figure>
  </div>
  <div class="column is-two-thirds content">
    <h2 class="title is-3 mt-2">About</h2>
    <p>
      <span class="has-text-weight-bold">ServerJockey</span> is a game server management system for
      <span class="has-text-weight-bold">Project Zomboid</span> and other supported games. It is designed
      to be an easy to use self-hosting option for multiplayer servers, allowing you to create and remotely
      manage your servers. Both this webapp and Discord can be used to manage servers. However to
      use Discord you will need to <a href="/guides/discord/setup">setup a discord bot</a> first.
    </p>
    <p class="has-text-weight-bold">
      Join the ServerJockey Discord
    </p>
    <div class="columns is-centered">
      <div class="column is-two-thirds">
        <a href="https://discord.gg/TEuurWAhHn" target="_blank">
          <figure class="image background-frame pl-4 pr-4 pt-4 pb-2">
            <img src="/assets/brands/discord_full_logo_black_RGB.svg"
                 alt="ServerJockey on Discord" title="ServerJockey on Discord" />
          </figure>
        </a>
      </div>
    </div>
    <p class="has-text-weight-bold">
      If you like using this system, please consider supporting it on Ko-fi
    </p>
    <div class="columns is-centered">
      <div class="column is-two-thirds">
        <a href="https://ko-fi.com/D1D4E4ZYZ" target="_blank">
          <figure class="image">
            <img src="/assets/brands/KoFi_SupportMe_dark.png"
                 alt="ServerJockey on Ko-fi" title="ServerJockey on Ko-fi" />
          </figure>
        </a>
      </div>
    </div>
    <p class="has-text-weight-bold">
      For instructional guides and dev updates, visit the YouTube channel
    </p>
    <div class="columns is-centered">
      <div class="column is-two-thirds">
        <a href="https://www.youtube.com/@BSALIS76" target="_blank">
          <figure class="image background-frame pl-5 pr-5 pt-4 pb-3">
            <img src="/assets/brands/yt_logo_rgb_light.png"
                 alt="ServerJockey on YouTube" title="ServerJockey on YouTube" />
          </figure>
        </a>
      </div>
    </div>
    <p class="has-text-weight-bold">
      Install instructions and source can be found on GitHub
    </p>
    <div class="columns is-centered">
      <div class="column is-half">
        <a href="https://github.com/SalSevenSix/serverjockey" target="_blank">
          <figure class="image background-frame pl-1 pr-1">
            <img src="/assets/brands/GitHub_Logo.png"
                 alt="ServerJockey on GitHub" title="ServerJockey on GitHub" />
          </figure>
        </a>
      </div>
    </div>
  </div>
</div>


<style>
  .background-frame {
    background-color: white;
    border-radius: 1em;
  }
</style>
