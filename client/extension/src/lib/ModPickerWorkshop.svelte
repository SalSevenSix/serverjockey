<script>
  import { dev } from '$app/environment';
  import { slide } from 'svelte/transition';

  const workshopFileBaseurl = 'https://steamcommunity.com/sharedfiles/filedetails/?id='

  export let workshop;
  export let items;

  let selectedVisible = false;

  $: togglerText = selectedVisible ? 'hide selected items' : 'show selected items';

  function toggleSelectedVisible() {
    selectedVisible = !selectedVisible;
  }

  function gotoWorkshopPage(item) {
    chrome.tabs.update({ active: true, url: workshopFileBaseurl + item });
  }
</script>


<div class="divider"><hr /></div>

<h2>Workshop Item</h2>
<p class="white-space-nowrap">
  {#if items.available}
    <button class="process" on:click={function() { items.add(); }}>Add</button>&nbsp;
  {:else}
    <button class="process" on:click={function() { items.remove(); }}>Remove</button>&nbsp;
  {/if}
  {workshop}
</p>

<button class="process is-wide" on:click={toggleSelectedVisible}>{togglerText}</button>
{#if selectedVisible}
  <div transition:slide={{ duration: 150 }}>
    <ul>
      {#each items.selected as item}
        <li>
          {#if dev}
            <a href={workshopFileBaseurl + item} target="_blank">{item}</a>
          {:else}
            <a href={'#'} on:click|preventDefault={function() { gotoWorkshopPage(item); }}>{item}</a>
          {/if}
        </li>
      {/each}
    </ul>
  </div>
{/if}
