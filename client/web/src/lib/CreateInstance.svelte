<script>
  import { dev } from '$app/env';
  import { createInstance } from '$lib/serverjockeyapi';

  let data = {};
  let creating = false;
	function create() {
	  creating = true;
	  createInstance(data, function() {
      creating = false;
      data.identity = null;
	  });
	}
</script>


<div class="block">
  <div class="field">
    <label for="module" class="label">Instance Type</label>
    <div class="control">
      <div class="select">
        <select id="module" bind:value={data.module}>
          {#if dev}<option>testserver</option>{/if}
          <option>projectzomboid</option>
          <option>factorio</option>
        </select>
      </div>
    </div>
  </div>
  <div class="field">
    <label for="instance" class="label">Instance Name</label>
    <div class="control">
      <input id="instance" class="input" type="text" bind:value={data.identity}>
    </div>
  </div>
  <div class="field">
    <div class="control">
      <button id="create" disabled={creating} name="create" class="button is-primary is-fullwidth" on:click={create}>Create</button>
    </div>
  </div>
</div>
