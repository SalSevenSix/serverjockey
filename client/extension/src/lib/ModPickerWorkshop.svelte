<script>
  import { dev } from '$app/environment';
  import { slide } from 'svelte/transition';

  export let workshop;
  export let items;

  let processing = false;
  let selectedVisible = false;

  $: togglerText = selectedVisible ? 'hide selected items' : 'show selected items';
  $: if (selectedVisible) { onSelectedVisible(); }

  async function onSelectedVisible() {
    if (processing) return;
    processing = true;
    while (processing && selectedVisible) {
      processing = await items.api.fetch();
    }
    processing = false;
  }

  function toggleSelectedVisible() {
    selectedVisible = !selectedVisible;
  }

  function gotoWorkshopPage(item) {
    chrome.tabs.update({ active: true, url: items.api.filebaseurl + item });
  }
</script>


<div class="divider"><hr /></div>

<h2>Workshop Item</h2>
<p id="modPickerWorkshopItem" class="white-space-nowrap">
  {#if items.available}
    <button id="modPickerWorkshopAdd" class="process" on:click={function() { items.add(); }}>Add</button>&nbsp;
  {:else}
    <button id="modPickerWorkshopRemove" class="process" on:click={function() { items.remove(); }}>Remove</button>&nbsp;
  {/if}
  {workshop}
</p>

<button id="modPickerWorkshopToggle" class="process is-wide" on:click={toggleSelectedVisible}>{togglerText}</button>
{#if selectedVisible}
  <div transition:slide={{ duration: 200 }}>
    <ol id="modPickerWorkshopSelected">
      {#each items.selected as item}
        <li>
          {#if dev}
            <a href={items.api.filebaseurl + item} target="_blank">{item}</a>&nbsp;
          {:else}
            <a href={'#'} on:click|preventDefault={function() { gotoWorkshopPage(item); }}>{item}</a>&nbsp;
          {/if}
          {#if items.api.name(item)}
            <button class="action cross" title="Remove"
                    on:click={function() { items.remove(item); }}>&nbsp;</button>
          {/if}
          {items.api.name(item)}
        </li>
      {/each}
    </ol>
  </div>
{/if}
