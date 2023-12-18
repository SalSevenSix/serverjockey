<script>
  import BackToTop from '$lib/BackToTop.svelte';
</script>


<div class="columns">
  <div class="column is-one-quarter content mb-0 pb-0">
    <figure class="image mt-1 max-300">
      <img src="/assets/brands/browser_extension.svg" alt="Browser Extension logo" />
    </figure>
  </div>
  <div class="column is-three-quarters content">
    <h2 class="title is-3 mt-2">Browser Extension</h2>
    <p>
      ServerJockey has a browser extension for
      <a href="https://www.google.com/chrome" target="_blank">Chrome <i class="fa fa-up-right-from-square"></i></a>
      that can be used to manage mods for Project Zomboid servers.
      This guide will show you how to install and use this extension.
    </p>
  </div>
</div>

<div class="content">
  <hr />
  <p><span class="step-title"></span>
    First step is to
    <a href="https://chromewebstore.google.com/detail/serverjockey/bcgjnafdidbpegbeijnbpaioipfckiaj" target="_blank">
      download and install the extension <i class="fa fa-up-right-from-square"></i></a> from the web store using
    the Chrome browser. First click the <span class="has-text-weight-bold">Add to Chrome</span> button on the page
    then the <span class="has-text-weight-bold">Add extension</span> button on the confirmation popup.
  </p>
  <figure class="image max-844">
    <img src="/assets/guides/extension/extension_page.jpg" alt="Extension page" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    After the extension is installed, you can optionally pin the extension to the menu bar for ease of access.
    To do this, open the extensions popup using the jigsaw button then click the pin button for
    the ServerJockey extension. The rest of the guide assumes the extension is pinned.
  </p>
  <figure class="image max-600">
    <img src="/assets/guides/extension/pin_extension.png" alt="Pin Extension" />
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
    Mods in the <span class="has-text-weight-bold">Selected Mods</span>
    can be re-ordered using the chevron buttons, and be removed with the cross button.
    Remember to click the <span class="has-text-weight-bold">Save</span>
    button to save the changes to the INI file of the selected instance.
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
    These lists function the same as the mod lists. Note that the base
    &nbsp;<span class="is-family-monospace">Muldraugh, KY</span>&nbsp;
    map should always be at the bottom.
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
