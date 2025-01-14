<script>
  import { onMount } from 'svelte';
  import { fNoop, noStorage } from '$lib/util/util';

  export let onAfterToggle = fNoop;

  const fontSizes = ['base-font-size-default', 'base-font-size-big', 'base-font-size-huge'];

  let fontSizeLink;
  let fontSizeIndex = 0;

  function setFontSize(oldFontSize, newFontSize) {
    if (!document) return;
    if (!document.documentElement) return;
    if (oldFontSize) { document.documentElement.classList.remove(oldFontSize); }
    document.documentElement.classList.add(newFontSize);
  }

  function toggleFontSize() {
    if (fontSizeLink.blur) { fontSizeLink.blur(); }
    const oldFontSize = fontSizes[fontSizeIndex];
    fontSizeIndex = fontSizeIndex >= fontSizes.length - 1 ? 0 : fontSizeIndex + 1;
    setFontSize(oldFontSize, fontSizes[fontSizeIndex]);
    if (!noStorage) {
      localStorage.setItem('sjgmsFontSizeIndex', fontSizeIndex.toString());
    }
    onAfterToggle();
  }

  onMount(function() {
    if (!noStorage) {
      const storedFontSizeIndex = localStorage.getItem('sjgmsFontSizeIndex');
      fontSizeIndex = storedFontSizeIndex ? parseInt(storedFontSizeIndex, 10) : 0;
    }
    setFontSize(null, fontSizes[fontSizeIndex]);
  });
</script>


<a id="navbarFontSize" bind:this={fontSizeLink} href={'#'} class="navbar-item"
   on:click|preventDefault={toggleFontSize}>&nbsp;<i class="fa fa-text-height fa-lg"></i>&nbsp;</a>
