<div class="overlay">
  <div class="inner">
    <slot />
  </div>
</div>


<style>
  .overlay {
    position: absolute;
    width: 100%;
    height: 100%;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0,0,0,0.3);
    z-index: 10;
  }

  .inner {
    padding-top: 15vh;
    padding-left: 30%;
  }
</style>
