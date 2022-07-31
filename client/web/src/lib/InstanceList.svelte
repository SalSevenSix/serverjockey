<script>
  import { onMount, onDestroy } from 'svelte';
  import { goto } from '$app/navigation';
	import { baseurl, instance, serverStatus, newGetRequest, newPostRequest, SubscriptionHelper } from '$lib/serverjockeyapi';

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
      if (data.event === 'created') {
        data.instance.url = baseurl + '/instances/' + data.instance.identity;
        instances = [...instances, data.instance];
      } else if (data.event === 'deleted') {
        instances = instances.filter(function(value) {
          return value.identity != data.instance.identity;
        });
      }
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

	function deleteInstance() {
	  let selected = instances[this.name];
	  if (!confirm('Delete ' + selected.identity + ' ?')) return;
    fetch(selected.url + '/server/delete', newPostRequest())
      .then(function(response) { if (!response.ok) throw new Error('Status: ' + response.status); })
      .catch(function(error) { alert('Error ' + error); });
	}
</script>


<div class="block">
  <h2 class="title is-5">Instances</h2>
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
          <td class="buttons">
            <button id="instancelist-view-{index}" name={index} class="button is-primary" on:click={viewInstance}>View</button>
            <button id="instancelist-delete-{index}" name={index} class="button is-danger" on:click={deleteInstance}>Delete</button>
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>
