<script>
  import { fNoop } from '$lib/util/util';

  export let showOnPx = 1000;

  let hidden = true;

  function gotoTop() {
    document.body.scrollIntoView();
  }

  function getContainer() {
    return document.documentElement || document.body;
  }

  function handleOnScroll() {
    if (!getContainer()) return;
    hidden = getContainer().scrollTop <= showOnPx;
  }
</script>


<svelte:window on:scroll={handleOnScroll} />

<div id="backToTop" class="back-to-top" class:hidden role="button" tabindex="0" on:click={gotoTop} on:keypress={fNoop}>
  <i class="fa fa-circle-up fa-3x"></i>
</div>


<style>
  .back-to-top {
    opacity: 1;
    transition: opacity 0.5s, visibility 0.5s;
    position: fixed;
    z-index: 99;
    user-select: none;
    cursor: pointer;
    right: 1.2em;
    bottom: 1.2em;
  }

  .back-to-top.hidden {
    opacity: 0;
    visibility: hidden;
  }
</style>
