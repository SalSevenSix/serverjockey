<script>
  export let data;
</script>


<h2>Available Mod IDs</h2>
<ul>
  {#each data.available.mods as mod}
    <li>
      <button class="action" on:click={function() { data.addModBottom(mod); }}>W</button>
      <button class="action" on:click={function() { data.addModTop(mod); }}>V</button>
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
        <button class="action" on:click={function() { data.removeMod(mod); }}>X</button>
        <button class="action" on:click={function() { data.bumpModUp(mod); }}>^</button>
        <button class="action" on:click={function() { data.bumpModDown(mod); }}>v</button>
        {mod}
      </li>
    {:else}
      <li>&nbsp;&nbsp; {mod}</li>
    {/if}
  {/each}
</ol>
