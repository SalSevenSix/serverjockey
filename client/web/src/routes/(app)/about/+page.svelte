<script>
  import { surl } from '$lib/util/sjgmsapi';
  import RubiksCube from '$lib/svg/RubiksCube.svelte';
  import ExtLink from '$lib/widget/ExtLink.svelte';
</script>


<div class="columns">
  <div class="column is-one-third content mb-0">
    <figure class="image max-400"><RubiksCube dazzle /></figure>
  </div>
  <div class="column is-two-thirds content">
    <h2 class="title is-3 mt-2">About</h2>
    <p class="pb-2">
      <ExtLink href="https://serverjockey.net" notranslate>ServerJockey</ExtLink>
      is a game server management system for
      <span class="has-text-weight-bold">Project Zomboid</span>
      and other supported games. It is designed to be an easy to use self-hosting option
      for multiplayer servers, allowing you to create and remotely manage your servers.
      Both this webapp and Discord can be used to manage servers.
    </p>
    <p class="has-text-weight-bold">
      <i class="fa fa-chevron-circle-right fa-lg"></i>&nbsp;
      Join the ServerJockey Discord
    </p>
    <div class="columns is-centered">
      <div class="column is-two-thirds">
        <a id="aboutPageDiscord" href="https://discord.gg/TEuurWAhHn" target="_blank">
          <figure class="image background-frame pl-5 pr-5 pt-3 pb-2">
            <img src={surl('/assets/brands/discord_full_logo_black_RGB.svg')}
                 alt="ServerJockey on Discord" title="ServerJockey on Discord" />
          </figure>
        </a>
      </div>
    </div>
    <p class="has-text-weight-bold">
      <i class="fa fa-chevron-circle-right fa-lg"></i>&nbsp;
      If you like using this system, please consider supporting it on Ko-fi
    </p>
    <div class="columns is-centered">
      <div class="column is-two-thirds">
        <a id="aboutPageKofi" href="https://ko-fi.com/serverjockey" target="_blank">
          <figure class="image background-frame pl-5 pr-5 pt-1 pb-0">
            <img src={surl('/assets/brands/kofi_logo.png')}
                 alt="ServerJockey on Ko-fi" title="ServerJockey on Ko-fi" />
          </figure>
        </a>
      </div>
    </div>
    <p class="has-text-weight-bold">
      <i class="fa fa-chevron-circle-right fa-lg"></i>&nbsp;
      For instructional guides and dev updates, visit the YouTube channel
    </p>
    <div class="columns is-centered">
      <div class="column is-two-thirds">
        <a id="aboutPageYoutube" href="https://www.youtube.com/channel/UCprGg-h1FbXwZ5HdRanbijw" target="_blank">
          <figure class="image background-frame pl-5 pr-5 pt-4 pb-3">
            <img src={surl('/assets/brands/yt_logo_rgb_light.png')}
                 alt="ServerJockey on YouTube" title="ServerJockey on YouTube" />
          </figure>
        </a>
      </div>
    </div>
    <p class="has-text-weight-bold">
      <i class="fa fa-chevron-circle-right fa-lg"></i>&nbsp;
      Install instructions and source can be found on GitHub
    </p>
    <div class="columns is-centered">
      <div class="column is-two-thirds">
        <a id="aboutPageGithub" href="https://github.com/SalSevenSix/serverjockey" target="_blank">
          <figure class="image background-frame pl-5 pr-5 pt-3 pb-3">
            <img src={surl('/assets/brands/GitHub_Lockup_Dark.svg')}
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
    border: 1px solid var(--color-standard-light-bwg);
    border-radius: 16px;
  }
</style>
