<script>
  import { browserName } from '$lib/util/util';
  import BackToTop from '$lib/widget/BackToTop.svelte';

  const isChrome = browserName === 'Chrome';
  const isEdge = browserName === 'Edge';
</script>


<div class="columns">
  <div class="column is-one-quarter content mb-0 pb-0">
    <figure class="image mt-1 max-300">
      <img src="/assets/guides/extension/browser_extension.svg" alt="Browser Extension logo" />
    </figure>
  </div>
  <div class="column is-three-quarters content">
    <h2 class="title is-3 mt-2">Browser Extension</h2>
    <p>
      ServerJockey has a browser extension for
      {#if isChrome || isEdge}
        <a href="https://www.google.com/chrome" target="_blank">Google Chrome
          <i class="fa fa-up-right-from-square"></i></a> and
        <a href="https://www.microsoft.com/en-us/edge" target="_blank">Microsoft Edge
          <i class="fa fa-up-right-from-square"></i></a>
      {:else}
        Google Chrome and Microsoft Edge
      {/if}
      that can be used to manage mods for Project Zomboid servers.
      This guide will show you how to install and use this extension.
    </p>
  </div>
</div>

<div class="content">
  <hr />
  {#if isChrome}
    <p><span class="step-title"></span>
      First step is to
      <a href="https://chromewebstore.google.com/detail/serverjockey/bcgjnafdidbpegbeijnbpaioipfckiaj"
         target="_blank">download and install the extension <i class="fa fa-up-right-from-square"></i></a>
      from the Chrome web store.
      First click the <span class="has-text-weight-bold">Add to Chrome</span> button on the page then the
      <span class="has-text-weight-bold">Add extension</span> button on the confirmation popup.
    </p>
    <figure class="image max-844">
      <img src="/assets/guides/extension/chrome_extension_page.jpg" alt="Chrome extension page" />
    </figure>
  {:else if isEdge}
    <p><span class="step-title"></span>
      First step is to
      <a href="https://microsoftedge.microsoft.com/addons/detail/serverjockey/fcfknahceaoeohgehmbialifgdbihloe"
         target="_blank">download and install the extension <i class="fa fa-up-right-from-square"></i></a>
      from the Edge website.
      First click the <span class="has-text-weight-bold">Get</span> button on the page then the
      <span class="has-text-weight-bold">Add extension</span> button on the confirmation popup.
    </p>
    <figure class="image max-844">
      <img src="/assets/guides/extension/edge_extension_page.png" alt="Edge extension page" />
    </figure>
  {:else}
    <p class="pb-3"><span class="step-title"></span>
      First step is to download and install either
      <a href="https://www.google.com/chrome" target="_blank">
        Chrome browser <i class="fa fa-up-right-from-square"></i></a> or
      <a href="https://www.microsoft.com/en-us/edge/download" target="_blank">
        Edge browser <i class="fa fa-up-right-from-square"></i></a>
      then return to this guide using that browser. Then download and install the
      <a href="https://chromewebstore.google.com/detail/serverjockey/bcgjnafdidbpegbeijnbpaioipfckiaj"
         target="_blank">Chrome extension <i class="fa fa-up-right-from-square"></i></a> or
      <a href="https://microsoftedge.microsoft.com/addons/detail/serverjockey/fcfknahceaoeohgehmbialifgdbihloe"
         target="_blank">Edge extension <i class="fa fa-up-right-from-square"></i></a> accordingly.
    </p>
    <div class="columns is-gapless is-tablet">
      <div class="column is-one-fifth"></div>
      <div class="column is-one-fifth content">
        <a href="https://www.google.com/chrome" title="Download Chrome" target="_blank">
          <i class="fa-brands fa-chrome fa-6x theme-black-white"></i></a>
      </div>
      <div class="column is-one-fifth content">
        <i class="fa fa-cloud-arrow-down fa-5x theme-black-white"></i>
      </div>
      <div class="column is-one-fifth content">
        <a href="https://www.microsoft.com/en-us/edge/download" title="Download Edge" target="_blank">
          <i class="fa-brands fa-edge fa-6x theme-black-white"></i></a>
      </div>
      <div class="column is-one-fifth"></div>
    </div>
  {/if}
</div>

<div class="content">
  <p><span class="step-title"></span>
    After the extension is installed, you can optionally pin the extension to the menu bar for ease of access.
    To do this, open the extensions popup using the jigsaw button then click the
    <span class="has-text-weight-bold">{isEdge ? 'Show in toolbar' : 'Pin'}</span>
    button for the ServerJockey extension. The rest of the guide assumes the extension is pinned.
  </p>
  <figure class="image max-500">
    {#if isEdge}
      <img src="/assets/guides/extension/edge_pin_extension.png" alt="Pin Edge extension" />
    {:else}
      <img src="/assets/guides/extension/chrome_pin_extension.png" alt="Pin Chrome extension" />
    {/if}
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    The extension can only be opened on the <a href="https://steamcommunity.com" target="_blank">Steam Community site
      <i class="fa fa-up-right-from-square"></i></a> with features only available on Project Zomboid Workshop mod pages.
    To begin, navigate to a mod page on the workshop, then open the extension panel with the pinned button.
    When opening the extension panel for the first time, you will need to connect the extension to your
    ServerJockey system. Enter the URL for the ServerJockey webapp and the login token,
    then click <span class="has-text-weight-bold">Connect</span>.
  </p>
  <figure class="image max-844">
    <img src="/assets/guides/extension/mod_britas_login.jpg" alt="Connect to ServerJockey" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    If needed, select the Project Zomboid instance using the dropdown.
    Note that the extension requires the instance to have a valid INI file.
    When on a Project Zomboid workshop mod page, you should see an
    <span class="has-text-weight-bold">Add</span> button.
    Click the button to add the workshop item.
  </p>
  <figure class="image max-844">
    <img src="/assets/guides/extension/mod_britas_add.jpg" alt="Add the workshop item" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    After adding a workshop item, you will be given options to add, order and remove mods within the workshop item.
    Mods will be shown under <span class="has-text-weight-bold">Available Mods</span>.
    Click a down arrow button to add the mod to the bottom (first button) or top (second button)
    of the <span class="has-text-weight-bold">Selected Mods</span> list.
  </p>
  <figure class="image max-844">
    <img src="/assets/guides/extension/mod_britas_available.jpg" alt="Available mods" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Mods in the <span class="has-text-weight-bold">Selected Mods</span> list
    can be re-ordered using the chevron buttons, or be removed with the cross button.
    Remember to click the <span class="has-text-weight-bold">Save</span>
    button to commit changes to the INI file of the selected instance.
    Note that the server will need to be restarted for these changes to take effect.
  </p>
  <figure class="image max-844">
    <img src="/assets/guides/extension/mod_britas_selected.jpg" alt="Selected mods" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Map mods are also supported. Another section will be shown with
    <span class="has-text-weight-bold">Available Maps</span> and
    <span class="has-text-weight-bold">Selected Maps</span>.
    These lists function the same as the mod lists. Note that the base map
    &nbsp;<span class="is-family-monospace notranslate">Muldraugh, KY</span>&nbsp;
    should always be at the bottom.
  </p>
  <figure class="image max-844">
    <img src="/assets/guides/extension/mod_chinatown_available.jpg" alt="Map mod" loading="lazy" />
  </figure>
</div>

<BackToTop />


<style>
  figure.max-844 img {
    max-width: 844px;
  }
</style>
