<script>
  import { onMount, onDestroy } from 'svelte';
  import { goto } from '$app/navigation';
	import { baseurl, instance, newGetRequest, serverStatus, SubscriptionHelper } from '$lib/serverjockeyapi';

  instance.set({});
  serverStatus.set({});

  let instances = [];
  let subs = new SubscriptionHelper();

	onMount(async function() {
    const result = await fetch(baseurl + '/instances', newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .catch(function(error) { alert(error); });
    Object.keys(result).forEach(function(key) {
      instances = [...instances, { identity: key, module: result[key].module, url: result[key].url }];
    });
    await subs.start(baseurl + '/instances/subscribe', function(data) {
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
	    return true;
	  });
  });

	onDestroy(function() {
		subs.stop();
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
          <td><button id="instancelist-view-{index}" name={index} class="button is-small is-primary" on:click={viewInstance}>View</button></td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>
