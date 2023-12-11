<script>
  export let workshop;
  export let items;
</script>


<div class="divider"><hr /></div>

<h2>Workshop Item</h2>
<p>
  {#if items.available}
    <button class="process" on:click={function() { items.add(); }}>Add</button>&nbsp;
  {:else}
    <button class="process" on:click={function() { items.remove(); }}>Remove</button>&nbsp;
  {/if}
  {workshop}
</p>
