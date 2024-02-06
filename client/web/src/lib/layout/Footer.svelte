<script>
  import TranslateControls from '$lib/layout/TranslateControls.svelte';
  import SocialsBar from '$lib/layout/SocialsBar.svelte';
</script>


<div class="block pt-5"></div>
<hr />

<div class="columns is-gapless is-mobile">
  <div class="column">
    <TranslateControls />
  </div>
  <div class="column">
    <SocialsBar />
  </div>
</div>

<div id="footerPadding"></div>


<style>
  #footerPadding {
    margin-bottom: 120px;
  }
</style>
