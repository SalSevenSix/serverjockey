<script>
  import { onMount, getContext } from 'svelte';
  import { dev } from '$app/environment';
  import { fly } from 'svelte/transition';
  import { newGetRequest, newPostRequest, logError } from '$lib/sjgmsapi';
  import { devDom, isModPage, processResults } from '$lib/ModPicker';
  import ModPickerWorkshop from '$lib/ModPickerWorkshop.svelte';
  import ModPickerItem from '$lib/ModPickerItem.svelte';

  const instance = getContext('instance');

  let processing = true;
  let dataSynced = false;
  let data = null;

  $: cannotSave = !data || processing || dataSynced;
  $: if ($instance) { fetchDom(); }

  function updated() {
    data = data;  // Ugly but svelte is not tracking internal changes
    dataSynced = false;
  }

  function saveIni() {
    processing = true;
    let request = newPostRequest('text/plain');
    request.body = data.generateIni();
    fetch($instance.url + '/config/ini', request)
      .then(function(response) {
        if (!response.ok) { throw new Error('Status: ' + response.status); }
        dataSynced = true;
      })
      .catch(logError)
      .finally(function() { processing = false; });
  }

  function fetchIni(dom) {
    processing = true;
    fetch($instance.url + '/config/ini', newGetRequest())
      .then(function(response) {
        if (!response.ok) { throw new Error('Status: ' + response.status); }
        return response.text();
      })
      .then(function(ini) {
        data = processResults(dom, ini, updated);
        dataSynced = true;
      })
      .catch(logError)
      .finally(function() { processing = false; });
  }

  function fetchDom() {
    data = null;
    if (dev) {
      fetchIni(devDom);
      return;
    }
    chrome.tabs.query({ active: true, lastFocusedWindow: true }).then(function(tabs) {
      if (tabs && tabs.length > 0) {
        chrome.tabs.sendMessage(tabs[0].id, { name: 'serverjockey-send-dom' }).then(function(dom) {
          if (isModPage(dom)) { fetchIni(dom); }
        });
      }
    });
  }

  if (!dev) {
    chrome.tabs.onUpdated.addListener(function(tabId, changeInfo, tabInfo) {
      if (!tabInfo.active) return;
      if (changeInfo.status === 'complete') { fetchDom(); } else { data = null; }
    });
    chrome.tabs.onActivated.addListener(function(activeInfo) {
      chrome.tabs.get(activeInfo.tabId).then(function(tab) {
        if (!tab.url) return;
        fetchDom();
      });
    });
  }

  onMount(fetchDom);
</script>


{#if data}
  <div in:fly={{ duration: 300, x: -200 }}>
    <ModPickerWorkshop workshop={data.dom.workshop} items={data.workshop} />
    {#if !data.workshop.available}
      <div in:fly={{ duration: 300, x: -200 }}>
        <ModPickerItem itemName="Mods" items={data.mods} source={data.dom.mods} />
        {#if data.dom.maps.length > 0}
          <ModPickerItem itemName="Maps" items={data.maps} source={data.dom.maps} />
        {/if}
      </div>
    {/if}
    <div class="save-button">
      <button class="process hero" disabled={cannotSave} on:click={saveIni}>{processing ? '...' : 'Save'}</button>
    </div>
  </div>
{:else}
  <div>
    <p><br />&nbsp; ...</p>
  </div>
{/if}


<style>
  .save-button {
    margin: 24px 0px 100px 0px;
  }
</style>
