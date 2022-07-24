<script>
  import { onMount, onDestroy } from 'svelte';
  import { goto } from '$app/navigation';
	import { baseurl, instance, subscribeAndPoll, serverStatus } from '$lib/serverjockeyapi';

  instance.set({});
  serverStatus.set({});

  let instances = [];
  let polling = true;
	onMount(async function loadInstances() {
    const result = await fetch(baseurl + '/instances')
      .then(function(response) { return response.json(); })
      .catch(function(error) { alert(error); });
    Object.keys(result).forEach(function(key) {
      instances = [...instances, { identity: key, module: result[key].module, url: result[key].url }];
    });
    subscribeAndPoll(baseurl + '/instances/subscribe', function(data) {
	    if (data == null || !polling) return polling;
	    data.url = baseurl + '/instances/' + data.identity;
	    let found = false;
	    let newInstances = [];
	    instances.forEach(function(value) {
	      if (data.identity === value.identity) {
	        found = true;
	      } else {
	        newInstances.push(value);
	      }
	    });
	    if (!found) {
	      newInstances.push(data);
	    }
	    instances = newInstances;
	    return polling;
	  });
  });

	onDestroy(function() {
		polling = false;
	});

	function viewInstance() {
	  let selected = instances[this.name];
		instance.set(selected);
		goto('/servers/' + selected.module);
	}
</script>


<div class="block">
  <table class="table">
    <thead>
      <tr>
        <th>Name</th>
        <th>Module</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      {#each instances as instance, index}
        <tr>
          <td>{instance.identity}</td>
          <td>{instance.module}</td>
          <td><button id="view-{index}" name={index} class="button is-small is-primary" on:click={viewInstance}>View</button></td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>
