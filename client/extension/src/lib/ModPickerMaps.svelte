<script>
  export let data;
</script>


<h2>Available Map Folders</h2>
<ul>
  {#each data.available.maps as map}
    <li>
      <button class="action arrow-down-to-line" title="Add to bottom"
              on:click={function() { data.addMapBottom(map); }}></button>
      <button class="action arrow-down" title="Add to top"
              on:click={function() { data.addMapTop(map); }}></button>
      {map}
    </li>
  {/each}
</ul>
{#if data.available.maps.length === data.dom.maps.length}
  <p class="text-warning">&nbsp; *** no maps selected ***</p>
{/if}

<h2>Selected Map Folders</h2>
<ol>
  {#each data.selected.maps as map}
    {#if data.dom.maps.includes(map)}
      <li>
        <button class="action cross" title="Remove" on:click={function() { data.removeMap(map); }}></button>
        <button class="action chevron-up" title="Move up" on:click={function() { data.bumpMapUp(map); }}></button>
        <button class="action chevron-down" title="Move down" on:click={function() { data.bumpMapDown(map); }}></button>
        {map}
      </li>
    {:else}
      <li>&nbsp;&nbsp; {map}</li>
    {/if}
  {/each}
</ol>
