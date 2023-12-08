<script>
  import { onMount } from 'svelte';
  import { getContext } from 'svelte';
  import { newGetRequest, newPostRequest } from '$lib/sjgmsapi';
  import { isModPage, processResults } from '$lib/ModPicker';

  const instance = getContext('instance');

  let data = null;

  function postIni() {
    let request = newPostRequest('text/plain');
    request.body = data.generateIni();
    fetch($instance.url + '/config/ini', request)
      .then(function(response) {
        if (!response.ok) { throw new Error('Status: ' + response.status); }
      })
      .catch(function(error) {
        console.error(error);
      });
  }

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
    <p>
      {#if data.available.workshop}
        <button on:click={function() { data.addWorkshop(); data = data; }}>Add</button>
      {:else}
        <button on:click={function() { data.removeWorkshop(); data = data; }}>Remove</button>
      {/if}
      &nbsp;&nbsp; {data.dom.workshop}
    </p>
    <ol>
      {#each data.selected.workshops as workshop}
        <li>{workshop} {data.dom.workshop === workshop ? '*' : ''}</li>
      {/each}
    </ol>
    {#if !data.available.workshop}
      <p>Available Mod IDs</p>
      <ol>
        {#each data.available.mods as mod}
          <li>
            <button on:click={function() { data.addModBottom(mod); data = data; }}>W</button>
            <button on:click={function() { data.addModTop(mod); data = data; }}>V</button>
            {mod}
          </li>
        {/each}
      </ol>
      <p>Selected Mod IDs</p>
      <ol>
        {#each data.selected.mods as mod}
          {#if data.dom.mods.includes(mod)}
            <li>
              <button on:click={function() { data.removeMod(mod); data = data; }}>X</button>
              <button on:click={function() { data.bumpModUp(mod); data = data; }}>^</button>
              <button on:click={function() { data.bumpModDown(mod); data = data; }}>v</button>
              {mod}
            </li>
          {:else}
            <li>&nbsp;&nbsp; {mod}</li>
          {/if}
        {/each}
      </ol>
      {#if data.dom.maps.length > 0}
        <p>Available Map Folders</p>
        <ol>
          {#each data.available.maps as map}
            <li>
              <button on:click={function() { data.addMapBottom(map); data = data; }}>W</button>
              <button on:click={function() { data.addMapTop(map); data = data; }}>V</button>
              {map}
            </li>
          {/each}
        </ol>
        <p>Selected Map Folders</p>
        <ol>
          {#each data.selected.maps as map}
            {#if data.dom.maps.includes(map)}
              <li>
                <button on:click={function() { data.removeMap(map); data = data; }}>X</button>
                <button on:click={function() { data.bumpMapUp(map); data = data; }}>^</button>
                <button on:click={function() { data.bumpMapDown(map); data = data; }}>v</button>
                {map}
              </li>
            {:else}
              <li>&nbsp;&nbsp; {map}</li>
            {/if}
          {/each}
        </ol>
      {/if}
    {/if}
    <p>
      <br />
      <button on:click={postIni}>SAVE</button>
    </p>
  {:else}
    <p>...</p>
  {/if}
</div>
