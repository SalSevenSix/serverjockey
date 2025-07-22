<script>
  import { onMount, onDestroy } from 'svelte';
  import { notifyError } from '$lib/util/notifications';
  import { confirmDangerModal } from '$lib/modal/modals';
  import { goto } from '$app/navigation';
  import { surl, newGetRequest, newPostRequest, SubscriptionHelper } from '$lib/util/sjgmsapi';
  import SpinnerIcon from '$lib/widget/SpinnerIcon.svelte';
  import ServerStateSymbol from '$lib/widget/ServerStateSymbol.svelte';

  const subs = new SubscriptionHelper();

  let instances = [];
  let loading = true;
  let deleting = false;

  function viewInstance(selected) {
    goto(surl('/servers/' + selected.module + '?i=' + selected.identity));
  }

  function deleteInstance(selected) {
    const message = 'Delete instance ' + selected.identity + '?\nThis action cannot be undone.';
    confirmDangerModal(message, selected.identity, function() {
      deleting = true;
      fetch(surl('/instances/' + selected.identity + '/server/delete'), newPostRequest())
        .then(function(response) { if (!response.ok) throw new Error('Status: ' + response.status); })
        .catch(function() { notifyError('Failed to delete ' + selected.identity); });
    });
  }

  function handleInstanceEvent(data) {
    if (data.event === 'status') {
      instances = instances.map(function(value) {
        if (value.identity != data.instance) return value;
        return { identity: value.identity, module: value.module, state: data.state };
      });
    } else if (data.event === 'created') {
      instances = [...instances, { identity: data.instance.identity, module: data.instance.module, state: null }];
    } else if (data.event === 'deleted') {
      instances = instances.filter(function(value) {
        return value.identity != data.instance.identity;
      });
      deleting = false;
    }
    return true;
  }

  onMount(function() {
    fetch(surl('/instances'), newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        Object.entries(json).forEach(function([identity, instance]) {
          instances = [...instances, { identity: identity, module: instance.module, state: instance.state }];
        });
        subs.start('/instances/subscribe', handleInstanceEvent);
      })
      .catch(function() { notifyError('Failed to load instances.'); })
      .finally(function() { loading = false; });
  });

  onDestroy(function() {
    subs.stop();
  });
</script>


<div class="content">
  <h2 class="title is-5">Instances</h2>
  <table class="table">
    <thead>
      <tr><th>Name</th><th>Module</th><th></th></tr>
    </thead>
    <tbody id="instanceList">
      {#if instances.length === 0}
        <tr><td colspan="3">
          {#if loading}
            <SpinnerIcon /> Loading...
          {:else}
            <i id="instanceListNoInstancesFound" class="fa fa-diamond fa-lg mr-1"></i> No instances found
          {/if}
        </td></tr>
      {:else}
        {#each instances as instance}
          <tr>
            <td class="word-break-all notranslate">
              <ServerStateSymbol state={instance.state} bigger />&nbsp; {instance.identity}
            </td>
            <td class="word-break-all notranslate">{instance.module}</td>
            <td class="buttons-column">
              <button name="instanceListViewI{instance.identity}" title="View"
                      class="button is-primary mb-1" disabled={deleting}
                      on:click={function() { viewInstance(instance); }}>
                <i class="fa fa-folder-open fa-lg"></i></button>
              <button name="instanceListDeleteI{instance.identity}" title="Delete"
                      class="button is-danger ml-1" disabled={deleting}
                      on:click={function() { deleteInstance(instance); }}>
                <i class="fa fa-trash-can fa-lg"></i></button>
            </td>
          </tr>
        {/each}
      {/if}
    </tbody>
  </table>
  {#if !loading && instances.length === 0}
    <p>
      For help creating a new game server, see the
      <a href={surl('/guides#gameserverguides')}>the guides</a>
    </p>
  {/if}
</div>


<style>
  .buttons-column {
    width: 33%;
    text-align: right;
  }

  .fa-folder-open {
    width: 1.5em;
  }
</style>
