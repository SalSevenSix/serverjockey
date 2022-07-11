<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
	import { loadInstances, instances, instance } from '$lib/serverjockeyapi';

	function viewInstance() {
	  let selected = $instances[this.name];
		instance.set(selected);
		goto('/servers/' + selected.module);
	}

	function deleteInstance() {
	  alert('Not implemented');
	}

	onMount(loadInstances);
</script>


<ul>
  {#each $instances as instance, index}
    <li>
      {instance.name} ({instance.module})
      <button id="view-{index}" name={index} class="button is-small is-primary" on:click={viewInstance}>View</button>
      <button id="delete-{index}" name={index} class="button is-small is-danger" on:click={deleteInstance}>Delete</button>
    </li>
  {:else}
    <li>loading...</li>
  {/each}
</ul>
