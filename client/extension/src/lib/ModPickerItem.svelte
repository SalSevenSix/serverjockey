<script>
  export let itemName;
  export let items;
  export let source;
</script>


<div class="divider"><hr /></div>

<h2>Available {itemName}</h2>
<ul>
  {#each items.available as item}
    <li>
      <button class="action arrow-down-to-line" title="Add to bottom"
              on:click={function() { items.addBottom(item); }}>&nbsp;</button>&nbsp;
      <button class="action arrow-down" title="Add to top"
              on:click={function() { items.addTop(item); }}>&nbsp;</button>&nbsp;
      {item}
    </li>
  {/each}
</ul>
{#if items.available.length === source.length}
  <p class="warning-text">&nbsp; no {itemName.toLowerCase()} selected</p>
{/if}

<h2>Selected {itemName}</h2>
<ol>
  {#each items.selected as item}
    {#if source.includes(item)}
      <li>
        <button class="action cross" title="Remove"
                on:click={function() { items.remove(item); }}>&nbsp;</button>
        <button class="action chevron-up" title="Move up"
                on:click={function() { items.bumpUp(item); }}>&nbsp;</button>
        <button class="action chevron-down" title="Move down"
                on:click={function() { items.bumpDown(item); }}>&nbsp;</button>
        {item}
      </li>
    {:else}
      <li>{item}</li>
    {/if}
  {/each}
</ol>
