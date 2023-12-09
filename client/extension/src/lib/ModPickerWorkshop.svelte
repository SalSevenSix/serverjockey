<script>
  export let data;
</script>


<h2>Workshop ID</h2>
<p>
  {#if data.available.workshop}
    <button class="action" on:click={function() { data.addWorkshop(); }}>Add</button>
  {:else}
    <button class="action" on:click={function() { data.removeWorkshop(); }}>Remove</button>
  {/if}
  &nbsp;&nbsp; {data.dom.workshop}
</p>
