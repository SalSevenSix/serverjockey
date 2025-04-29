<script>
  import { fNoop } from '$lib/util/util';

  export let showOnPx = 1000;

  let hidden = true;

  function onClick() {
    document.body.scrollIntoView();
  }

  function onScroll() {
    const container = document.documentElement || document.body;
    if (!container) return;
    hidden = container.scrollTop <= showOnPx;
  }
</script>


<svelte:window on:scroll={onScroll} />

<div id="backToTop" class="theme-background back-to-top" class:hidden role="button" tabindex="0"
     on:click={onClick} on:keypress={fNoop}>
  <i class="fa fa-circle-up fa-3x"></i>
</div>


<style>
  .back-to-top {
    border-radius: 50%;
    padding: 2px;
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
