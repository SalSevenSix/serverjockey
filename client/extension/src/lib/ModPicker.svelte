<script>
  import { onMount } from 'svelte';
  import { getContext } from 'svelte';
  import { newGetRequest } from '$lib/sjgmsapi';
  import { isModPage, processResults } from '$lib/ModPicker';

  const instance = getContext('instance');

  let data = null;

  function fetchIni(dom) {
    fetch($instance.url + '/config/ini', newGetRequest())
      .then(function(response) {
        if (!response.ok) { throw new Error('Status: ' + response.status); }
        return response.text();
      })
      .then(function(ini) {
        data = processResults(dom, ini);
      })
      .catch(function(error) {
        console.error(error);
      });
  }

  function fetchDom() {
    chrome.tabs.query({ active: true, lastFocusedWindow: true }).then(function(tabs) {
      if (tabs && tabs.length > 0) {
        chrome.tabs.sendMessage(tabs[0].id, { name: 'send-dom' }).then(function(dom) {
          if (isModPage(dom)) { fetchIni(dom); }
        });
      }
    });
  }

  chrome.tabs.onUpdated.addListener(function(tabId, changeInfo, tabInfo) {
    if (!tabInfo.active) return;
    if (changeInfo.status === 'complete') { fetchDom(); } else { data = null; }
  });

  onMount(fetchDom);
</script>


<div>
  {#if data}
    <p>Workshop ID</p>
    <p>{data.dom.workshop} {data.selectable.workshop ? 'o' : 'x'}</p>
    <p>Available Mod IDs</p>
    <ol>
      {#each data.selectable.mods as mod}
        <li>{mod}</li>
      {/each}
    </ol>
    <p>Current Mod IDs</p>
    <ol>
      {#each data.selected.mods as mod}
        <li>{mod} {data.dom.mods.includes(mod) ? '*' : ''}</li>
      {/each}
    </ol>
    {#if data.dom.maps.length > 0}
      <p>Available Map Folders</p>
      <ol>
        {#each data.selectable.maps as map}
          <li>{map} {data.dom.maps.includes(map) ? '*' : ''}</li>
        {/each}
      </ol>
      <p>Current Map Folders</p>
      <ol>
        {#each data.selected.maps as map}
          <li>{map}</li>
        {/each}
      </ol>
    {/if}
  {:else}
    <p>...</p>
  {/if}
</div>
