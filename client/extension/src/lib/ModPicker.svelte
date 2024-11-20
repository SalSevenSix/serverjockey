<script>
  import { onMount, getContext } from 'svelte';
  import { fly } from 'svelte/transition';
  import { dev } from '$app/environment';
  import { newGetRequest, newPostRequest, logError } from '$lib/sjgmsapi';
  import { devDom, domClean, isModPage } from '$lib/util';
  import { processResults } from '$lib/ModPicker';
  import ModPickerWorkshop from '$lib/ModPickerWorkshop.svelte';
  import ModPickerItem from '$lib/ModPickerItem.svelte';

  const instance = getContext('instance');

  let processing = true;
  let dataSynced = false;
  let data = null;

  $: cannotSave = !data || processing || dataSynced;
  $: if ($instance) { fetchDom(); }

  function updated(dirty=true) {
    data = data;  // Ugly but svelte is not tracking internal changes
    if (dirty) { dataSynced = false; }
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
          dom = domClean(dom);
          if (isModPage(dom)) { fetchIni(dom); } else { processing = false; }
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
  </div>
  <div class="footer-space"></div>
  <div in:fly={{ delay: 300, duration: 300, y: 80 }} class="save-button"><div>
    <button id="modPickerSave" class="process hero" disabled={cannotSave}
            on:click={saveIni}>{processing ? '...' : 'Save'}</button>
  </div></div>
{:else}
  <div class="no-mod-message">
    {#if processing}
      <p id="modPickerLoading">&nbsp;&nbsp;loading&nbsp;...</p>
    {:else}
      <p id="modPickerNoModFound" class="warning-text">mod details not found</p>
    {/if}
  </div>
{/if}
