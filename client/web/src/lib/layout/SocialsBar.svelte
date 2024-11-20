<script>
  import { surl } from '$lib/util/sjgmsapi';
</script>


<div class="block is-flex is-flex-direction-row is-justify-content-right is-flex-wrap-nowrap mr-1">
  <div class="block icon-container"><p class="has-text-right">
    <a id="socialsBarDiscord" href="https://discord.gg/TEuurWAhHn" target="_blank">
      <i class="fa-brands fa-discord fa-xl theme-black-white" title="ServerJockey on Discord"></i></a>
  </p></div>
  <div class="block icon-container ml-2"><p class="has-text-right">
    <a id="socialsBarKofi" href="https://ko-fi.com/serverjockey" target="_blank">
      <img id="kofiIcon" src={surl('/assets/brands/kofi_symbol.png')}
           alt="ServerJockey on Ko-fi" title="ServerJockey on Ko-fi" /></a>
  </p></div>
  <div class="block icon-container ml-1"><p class="has-text-right">
    <a id="socialsBarYoutube" href="https://www.youtube.com/channel/UCprGg-h1FbXwZ5HdRanbijw" target="_blank">
      <i class="fa-brands fa-youtube fa-xl theme-black-white" title="ServerJockey on YouTube"></i></a>
  </p></div>
  <div class="block icon-container ml-1"><p class="has-text-right">
    <a id="socialsBarGithub" href="https://github.com/SalSevenSix/serverjockey" target="_blank">
      <i class="fa-brands fa-github fa-xl theme-black-white" title="ServerJockey on GitHub"></i></a>
  </p></div>
</div>


<style>
  .icon-container {
    width: 45px;
  }

  #kofiIcon {
    width: 1.8663em;
    height: 1.5em;
  }
</style>
