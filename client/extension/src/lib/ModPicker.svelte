<script>
  import { onMount, getContext } from 'svelte';
  import { dev } from '$app/environment';
  import { newGetRequest, newPostRequest, logError } from '$lib/sjgmsapi';
  import { devDom, isModPage, processResults } from '$lib/ModPicker';
  import ModPickerWorkshop from '$lib/ModPickerWorkshop.svelte';
  import ModPickerItem from '$lib/ModPickerItem.svelte';

  const instance = getContext('instance');

  let cannotSave = true;
  let data = null;

  function updated() {
    data = data;  // Ugly but svelte is not tracking internal changes
    cannotSave = false;
  }

  function saveIni() {
    let request = newPostRequest('text/plain');
    request.body = data.generateIni();
    fetch($instance.url + '/config/ini', request)
      .then(function(response) {
        if (!response.ok) { throw new Error('Status: ' + response.status); }
        cannotSave = true;
      })
      .catch(logError);
  }

  function fetchIni(dom) {
    fetch($instance.url + '/config/ini', newGetRequest())
      .then(function(response) {
        if (!response.ok) { throw new Error('Status: ' + response.status); }
        return response.text();
      })
      .then(function(ini) {
        data = processResults(dom, ini, updated);
      })
      .catch(logError);
  }

  function fetchDom() {
    if (dev) {
      fetchIni(devDom);
    } else {
      chrome.tabs.query({ active: true, lastFocusedWindow: true }).then(function(tabs) {
        if (tabs && tabs.length > 0) {
          chrome.tabs.sendMessage(tabs[0].id, { name: 'send-dom' }).then(function(dom) {
            if (isModPage(dom)) { fetchIni(dom); }
          });
        }
      });
    }
  }

  if (!dev) {
    chrome.tabs.onUpdated.addListener(function(tabId, changeInfo, tabInfo) {
      if (!tabInfo.active) return;
      if (changeInfo.status === 'complete') { fetchDom(); } else { data = null; }
    });
  }

  onMount(fetchDom);
</script>


<div>
  {#if data}
    <ModPickerWorkshop workshop={data.dom.workshop} items={data.workshop} />
    {#if !data.workshop.available}
      <ModPickerItem itemName="Mods" items={data.mods} source={data.dom.mods} />
      {#if data.dom.maps.length > 0}
        <ModPickerItem itemName="Maps" items={data.maps} source={data.dom.maps} />
      {/if}
    {/if}
    <div class="save-button">
      <button class="process hero" disabled={cannotSave} on:click={saveIni}>Save</button>
    </div>
  {:else}
    <p><br />&nbsp; ...</p>
  {/if}
</div>


<style>
  .save-button {
    margin: 24px 0px 100px 0px;
  }
</style>
