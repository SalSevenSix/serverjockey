<script>
  import { surl } from '$lib/util/sjgmsapi';
</script>


<div class="block is-flex is-flex-direction-row is-justify-content-right is-flex-wrap-nowrap mr-1">
  <div class="block icon-container"><p class="has-text-right">
    <a href="https://discord.gg/TEuurWAhHn" target="_blank">
      <i class="fa-brands fa-discord fa-xl theme-black-white" title="ServerJockey on Discord"></i></a>
  </p></div>
  <div class="block icon-container ml-3"><p class="has-text-right">
    <a href="https://ko-fi.com/D1D4E4ZYZ" target="_blank">
      <img id="kofiIcon" src={surl('/assets/brands/ko-fi-icon.png')}
           alt="ServerJockey on Ko-fi" title="ServerJockey on Ko-fi" /></a>
  </p></div>
  <div class="block icon-container ml-1"><p class="has-text-right">
    <a href="https://www.youtube.com/@BSALIS76/videos" target="_blank">
      <i class="fa-brands fa-youtube fa-xl theme-black-white" title="ServerJockey on YouTube"></i></a>
  </p></div>
  <div class="block icon-container ml-1"><p class="has-text-right">
    <a href="https://github.com/SalSevenSix/serverjockey" target="_blank">
      <i class="fa-brands fa-github fa-xl theme-black-white" title="ServerJockey on GitHub"></i></a>
  </p></div>
</div>


<style>
  .icon-container {
    width: 45px;
  }

  #kofiIcon {
    width: 2.0625em;
    height: 1.4198em;
  }
</style>
