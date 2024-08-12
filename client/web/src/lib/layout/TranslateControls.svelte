<script>
  import { onMount, onDestroy } from 'svelte';
  import { sleep, noStorage } from '$lib/util/util';

  const storageKey = 'sjgmsTranslating';
  let oldLocation = window.location.href;
  let translating = false;

  function canTranslate() {
    if (typeof(google) === 'undefined') return false;
    if (typeof(google.translate) === 'undefined') return false;
    if (typeof(google.translate.TranslateElement) === 'undefined') return false;
    return true;
  }

  function enableTranslation() {
    if (!canTranslate()) return;
    translating = true;
    if (!noStorage) { localStorage.setItem(storageKey, 'true'); }
    new google.translate.TranslateElement({
      pageLanguage: 'en',
      includedLanguages: 'es,fr,it,de,ru,af,pl,pt,sv,fi,no,da,nl,el,ja,ko,zh-CN,vi,th,ar,iw',
      layout: google.translate.TranslateElement.InlineLayout.SIMPLE },
      'google_translate_element');
  }

  function disableTranslation() {
    translating = false;
    if (!noStorage) { localStorage.removeItem(storageKey); }
    window.location.reload();
  }

  const locationPoller = setInterval(function() {
    if (oldLocation === window.location.href) return;
    const thisLocation = window.location.href;
    oldLocation = thisLocation;
    if (!translating) return;
    sleep(1500).then(function() {
      if (thisLocation === window.location.href) {
        document.body.classList.add('force-refresh');
      }
    });
  }, 1000);

  onMount(function() {
    if (noStorage) return;
    if (localStorage.getItem(storageKey)) { enableTranslation(); }
  });

  onDestroy(function() {
    clearInterval(locationPoller);
  });
</script>


<div class="buttons" class:is-hidden={translating || !canTranslate()}>
  <button class="button is-dark is-small" title="Enable Google Translate" on:click={enableTranslation}>
    &nbsp;<i class="fa fa-language fa-xl"></i>&nbsp;&nbsp;&nbsp;Translate&nbsp;</button>
</div>

<div class:is-hidden={!translating}>
  <div class="block is-flex is-flex-direction-row is-flex-wrap-nowrap">
    <div class="buttons mr-1">
      <button class="button is-dark disable-button" title="Disable translation (page will be reloaded)"
              on:click={disableTranslation}><i class="fa fa-xmark"></i></button>
    </div>
    <div id="google_translate_element"></div>
  </div>
</div>


<style>
  .disable-button {
    font-size: 16px;
    width: 34px;
    height: 26px;
  }
</style>
