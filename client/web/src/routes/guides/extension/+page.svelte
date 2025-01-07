<script>
  import { browserName } from '$lib/util/util';
  import { surl } from '$lib/util/sjgmsapi';
  import Jigsaw from '$lib/svg/Jigsaw.svelte';
  import BackToTop from '$lib/widget/BackToTop.svelte';
  import ExtLink from '$lib/widget/ExtLink.svelte';

  const isChrome = browserName === 'Chrome';
  const isEdge = browserName === 'Edge';
</script>


<div class="columns">
  <div class="column is-one-quarter content mb-0 pb-0">
    <figure class="image max-200"><Jigsaw /></figure>
  </div>
  <div class="column is-three-quarters content">
    <h2 class="title is-3 mt-2">Browser Extension</h2>
    <p>
      ServerJockey has a browser extension for
      {#if isChrome || isEdge}
        <ExtLink href="https://www.google.com/chrome" notranslate>Google Chrome</ExtLink>
        and
        <ExtLink href="https://www.microsoft.com/en-us/edge" notranslate>Microsoft Edge</ExtLink>
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
      <ExtLink href="https://chromewebstore.google.com/detail/serverjockey/bcgjnafdidbpegbeijnbpaioipfckiaj"
               wrap>download and install the extension</ExtLink>
      from the Chrome web store. First click the
      <span class="has-text-weight-bold">Add to Chrome</span>
      button on the page then the
      <span class="has-text-weight-bold">Add extension</span>
      button on the confirmation popup.
    </p>
    <figure class="image max-1024">
      <img src={surl('/assets/guides/extension/chrome_extension_page.png')} alt="Chrome extension page" />
    </figure>
  {:else if isEdge}
    <p><span class="step-title"></span>
      First step is to
      <ExtLink href="https://microsoftedge.microsoft.com/addons/detail/serverjockey/fcfknahceaoeohgehmbialifgdbihloe"
               wrap>download and install the extension</ExtLink>
      from the Edge website. First click the
      <span class="has-text-weight-bold">Get</span>
      button on the page then the
      <span class="has-text-weight-bold">Add extension</span>
      button on the confirmation popup.
    </p>
    <figure class="image max-1024">
      <img src={surl('/assets/guides/extension/edge_extension_page.png')} alt="Edge extension page" />
    </figure>
  {:else}
    <p class="pb-3"><span class="step-title"></span>
      First step is to download and install either
      <ExtLink href="https://www.google.com/chrome">Chrome browser</ExtLink>
      or
      <ExtLink href="https://www.microsoft.com/en-us/edge/download">Edge browser</ExtLink>
      then return to this guide using that browser. Then download and install the
      <ExtLink href="https://chromewebstore.google.com/detail/serverjockey/bcgjnafdidbpegbeijnbpaioipfckiaj"
         >Chrome extension</ExtLink>
      or
      <ExtLink href="https://microsoftedge.microsoft.com/addons/detail/serverjockey/fcfknahceaoeohgehmbialifgdbihloe"
         >Edge extension</ExtLink>
      accordingly.
    </p>
    <div class="columns is-gapless is-tablet">
      <div class="column is-one-fifth"></div>
      <div class="column is-one-fifth content">
        <ExtLink href="https://www.google.com/chrome" title="Download Chrome"
                 wrap><i class="fa-brands fa-chrome fa-6x theme-black-white"></i></ExtLink>
      </div>
      <div class="column is-one-fifth content">
        <i class="fa fa-cloud-arrow-down fa-5x theme-black-white"></i>
      </div>
      <div class="column is-one-fifth content">
        <ExtLink href="https://www.microsoft.com/en-us/edge/download" title="Download Edge"
                 wrap><i class="fa-brands fa-edge fa-6x theme-black-white"></i></ExtLink>
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
      <img src={surl('/assets/guides/extension/edge_pin_extension.png')} alt="Pin Edge extension" />
    {:else}
      <img src={surl('/assets/guides/extension/chrome_pin_extension.png')} alt="Pin Chrome extension" />
    {/if}
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    The extension can only be opened on the
    <ExtLink href="https://steamcommunity.com" wrap>Steam Community site</ExtLink>
    with features only available on Project Zomboid Workshop mod pages.
    To begin, navigate to a mod page on the workshop, then open the extension panel with the pinned button.
    When opening the extension panel for the first time, you will need to connect the extension to your
    ServerJockey system. Enter the URL for the ServerJockey webapp and the login token, then click
    <span class="has-text-weight-bold notranslate">Connect</span>.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/extension/mod_britas_login.jpg')} alt="Connect to ServerJockey" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    If needed, select the Project Zomboid instance using the dropdown.
    Note that the extension requires the instance to have a valid INI file.
    When on a Project Zomboid workshop mod page, you should see an
    <span class="has-text-weight-bold notranslate">Add</span>
    button. Click the button to add the workshop item.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/extension/mod_britas_add.jpg')} alt="Add the workshop item" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    After adding a workshop item, you will be given options to add,
    order and remove mods within the workshop item. Mods will be shown under
    <span class="has-text-weight-bold notranslate">Available Mods</span>.
    Click a down arrow button to add the mod to the bottom (first button) or top (second button) of the
    <span class="has-text-weight-bold notranslate">Selected Mods</span>
    list.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/extension/mod_britas_available.jpg')} alt="Available mods" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Mods in the
    <span class="has-text-weight-bold notranslate">Selected Mods</span>
    list can be re-ordered using the chevron buttons, or be removed with the cross button. Remember to click the
    <span class="has-text-weight-bold notranslate">Save</span>
    button to commit changes to the INI file of the selected instance.
    Note that the server will need to be restarted for these changes to take effect.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/extension/mod_britas_selected.jpg')} alt="Selected mods" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Map mods are also supported. Another section will be shown with
    <span class="has-text-weight-bold notranslate">Available Maps</span>
    and
    <span class="has-text-weight-bold notranslate">Selected Maps</span>.
    These lists function the same as the mod lists. Note that the base map
    &nbsp;<span class="is-family-monospace notranslate">Muldraugh, KY</span>&nbsp;
    should always be at the bottom.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/extension/mod_chinatown_available.jpg')} alt="Map mod" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Click the
    <span class="has-text-weight-bold notranslate">show selected items</span>
    toggle button to show or hide the selected workshop items list.
    You are able to jump to any workshop item using the workshop ID link.
    Use the cross button to remove any workshop item, but remember to save changes.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/extension/mod_chinatown_workshops.jpg')} alt="Workshop list" loading="lazy" />
  </figure>
</div>

<BackToTop />
