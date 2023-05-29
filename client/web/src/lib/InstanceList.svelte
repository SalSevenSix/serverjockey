<script>
  import { onMount, onDestroy } from 'svelte';
  import { notifyError } from '$lib/notifications';
  import { confirmDangerModal } from '$lib/modals';
  import { goto } from '$app/navigation';
  import { baseurl, instance, serverStatus, newGetRequest, newPostRequest, SubscriptionHelper } from '$lib/sjgmsapi';

  instance.set({});
  serverStatus.set({});

  let subs = new SubscriptionHelper();
  let instances = [];
  let loading = true;

  onMount(function() {
    fetch(baseurl + '/instances', newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        Object.keys(json).forEach(function(key) {
          instances = [...instances, { identity: key, module: json[key].module, url: json[key].url }];
        });
        subs.start(baseurl + '/instances/subscribe', function(data) {
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
      })
      .catch(function(error) {
        notifyError('Failed to load instances.');
      })
      .finally(function() {
        loading = false;
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
    let message = 'Delete instance ' + selected.identity + '?\nThis action cannot be undone.';
    confirmDangerModal(message, selected.identity, function() {
      fetch(selected.url + '/server/delete', newPostRequest())
        .then(function(response) { if (!response.ok) throw new Error('Status: ' + response.status); })
        .catch(function(error) { notifyError('Failed to delete ' + selected.identity); });
    });
  }
</script>


<div class="content">
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
      {#if instances.length === 0}
        <tr><td colspan="3">
          {loading ? 'Loading...' : '0 instances found.'}
        </td></tr>
      {:else}
        {#each instances as instance, index}
          <tr>
            <td class="word-break-all">{instance.identity}</td>
            <td>{instance.module}</td>
            <td>
              <button name={index} class="button is-primary mb-1" title="View"
                      on:click={viewInstance}>&nbsp;<i class="fa fa-folder-open fa-lg"></i>&nbsp;</button>
              <button name={index} class="button is-danger ml-1" title="Delete"
                      on:click={deleteInstance}><i class="fa fa-trash-can fa-lg"></i></button>
            </td>
          </tr>
        {/each}
      {/if}
    </tbody>
  </table>
</div>
