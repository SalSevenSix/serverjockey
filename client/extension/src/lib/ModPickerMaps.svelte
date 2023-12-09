<script>
  export let data;
</script>


<h2>Available Map Folders</h2>
<ul>
  {#each data.available.maps as map}
    <li>
      <button class="action" on:click={function() { data.addMapBottom(map); }}>W</button>
      <button class="action" on:click={function() { data.addMapTop(map); }}>V</button>
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
        <button class="action" on:click={function() { data.removeMap(map); }}>X</button>
        <button class="action" on:click={function() { data.bumpMapUp(map); }}>^</button>
        <button class="action" on:click={function() { data.bumpMapDown(map); }}>v</button>
        {map}
      </li>
    {:else}
      <li>&nbsp;&nbsp; {map}</li>
    {/if}
  {/each}
</ol>
