<script>
  export let data;
</script>


<h2>Available Mod IDs</h2>
<ul>
  {#each data.available.mods as mod}
    <li>
      <button class="action arrow-down-to-line" title="Add to bottom"
              on:click={function() { data.addModBottom(mod); }}></button>
      <button class="action arrow-down" title="Add to top"
              on:click={function() { data.addModTop(mod); }}></button>
      {mod}
    </li>
  {/each}
</ul>
{#if data.available.mods.length === data.dom.mods.length}
  <p class="text-warning">&nbsp; *** no mods selected ***</p>
{/if}

<h2>Selected Mod IDs</h2>
<ol>
  {#each data.selected.mods as mod}
    {#if data.dom.mods.includes(mod)}
      <li>
        <button class="action cross" title="Remove" on:click={function() { data.removeMod(mod); }}></button>
        <button class="action chevron-up" title="Move up" on:click={function() { data.bumpModUp(mod); }}></button>
        <button class="action chevron-down" title="Move down" on:click={function() { data.bumpModDown(mod); }}></button>
        {mod}
      </li>
    {:else}
      <li>&nbsp;&nbsp; {mod}</li>
    {/if}
  {/each}
</ol>
