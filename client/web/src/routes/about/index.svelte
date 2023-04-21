<script>
  import RubiksCube from '$lib/RubiksCube.svelte';
</script>


<div class="columns">
  <div class="column is-one-third">
    <div class="pl-5 pr-6"><RubiksCube dazzle /></div>
  </div>
  <div class="column content is-two-thirds">
    <h2 class="title is-3 mt-2">About</h2>
    <p>
      <span class="has-text-weight-bold">ServerJockey</span> is a game server management system for
      <span class="has-text-weight-bold">Project Zomboid</span> and other supported games. It is designed
      to be an easy to use self-hosting option for multiplayer servers. Allowing you to create and remotely
      manage your servers. Both this webapp and Discord can be used to manage the servers. However to
      use Discord you will need to <a href="/guides/discord">setup a discord bot</a> first.
    </p>
    <p>
      If your like using this system, please consider supporting me on Ko-fi.
    </p>
    <div class="columns is-centered">
      <div class="column is-half">
        <a href="https://ko-fi.com/D1D4E4ZYZ" target="_blank">
          <figure>
            <img class="ko-fi-img" src="https://cdn.ko-fi.com/cdn/kofi2.png?v=3"
                 alt="Help support me at at ko-fi.com" />
          </figure>
        </a>
      </div>
    </div>
    <p>
      ServerJockey can be found on GitHub.
    </p>
    <div class="columns is-centered">
      <div class="column is-half">
        <a href="https://github.com/SalSevenSix/serverjockey" target="_blank">
          <figure>
            <img class="github-img" src="/assets/icons/GitHub_Logo.png"
                 alt="ServerJockey on GitHub" />
          </figure>
        </a>
      </div>
    </div>
  </div>
</div>


<style>
  .ko-fi-img {
    border: 0px;
    height: 36px;
  }

  .github-img {
    width: 128px;
  }
</style>
