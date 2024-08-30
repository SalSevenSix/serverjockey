<script>
  import { onMount, onDestroy } from 'svelte';
  import { notifyError } from '$lib/util/notifications';
  import { confirmDangerModal } from '$lib/modal/modals';
  import { goto } from '$app/navigation';
  import { surl, newGetRequest, newPostRequest, SubscriptionHelper } from '$lib/util/sjgmsapi';
  import SpinnerIcon from '$lib/widget/SpinnerIcon.svelte';

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
        .catch(function(error) { notifyError('Failed to delete ' + selected.identity); });
    });
  }

  function handleInstanceEvent(data) {
    if (data.event === 'running') {
      instances = instances.map(function(value) {
        if (value.identity != data.instance) return value;
        return { identity: value.identity, module: value.module, running: data.running };
      });
    } else if (data.event === 'created') {
      instances = [...instances, { identity: data.instance.identity, module: data.instance.module, running: false }];
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
        Object.keys(json).forEach(function(key) {
          instances = [...instances, { identity: key, module: json[key].module, running: json[key].running }];
        });
        subs.start('/instances/subscribe', handleInstanceEvent);
      })
      .catch(function(error) { notifyError('Failed to load instances.'); })
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
    <tbody>
      {#if instances.length === 0}
        <tr><td colspan="3">
          {#if loading}
            <SpinnerIcon /> Loading...
          {:else}
            <i class="fa fa-diamond fa-lg mr-1"></i> No instances found
          {/if}
        </td></tr>
      {:else}
        {#each instances as instance}
          <tr>
            <td class="word-break-all notranslate">
              <i class="fa {instance.running ? 'fa-play' : 'fa-stop'} fa-xl"></i>
              {instance.identity}
            </td>
            <td class="word-break-all notranslate">{instance.module}</td>
            <td class="buttons-column">
              <button title="View" class="button is-primary mb-1" disabled={deleting}
                      on:click={function() { viewInstance(instance); }}>
                <i class="fa fa-folder-open fa-lg"></i></button>
              <button title="Delete" class="button is-danger ml-1" disabled={deleting}
                      on:click={function() { deleteInstance(instance); }}>
                <i class="fa fa-trash-can fa-lg"></i></button>
            </td>
          </tr>
        {/each}
      {/if}
    </tbody>
  </table>
</div>


<style>
  .fa-play {
    width: 1em;
    color: var(--color-standard-success-def);
  }

  .fa-stop {
    width: 1em;
  }

  .buttons-column {
    width: 33%;
    text-align: right;
  }

  .fa-folder-open {
    width: 1.5em;
  }
</style>
