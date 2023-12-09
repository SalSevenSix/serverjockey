<script>
  export let data;
</script>


<h2>Workshop ID</h2>
<p>
  {#if data.available.workshop}
    <button class="process" on:click={function() { data.addWorkshop(); }}>Add</button>&nbsp;
  {:else}
    <button class="process" on:click={function() { data.removeWorkshop(); }}>Remove</button>&nbsp;
  {/if}
  {data.dom.workshop}
</p>
