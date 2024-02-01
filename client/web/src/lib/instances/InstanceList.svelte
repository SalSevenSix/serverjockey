<script>
  import { onMount, onDestroy } from 'svelte';
  import { notifyError } from '$lib/util/notifications';
  import { confirmDangerModal } from '$lib/modal/modals';
  import { goto } from '$app/navigation';
  import { newGetRequest, newPostRequest, buildUnstanceUrl, SubscriptionHelper } from '$lib/util/sjgmsapi';
  import SpinnerIcon from '$lib/widget/SpinnerIcon.svelte';

  const subs = new SubscriptionHelper();

  let instances = [];
  let loading = true;
  let deleting = false;

  function viewInstance(selected) {
    goto(buildUnstanceUrl(selected.module, selected.identity));
  }

  function deleteInstance(selected) {
    let message = 'Delete instance ' + selected.identity + '?\nThis action cannot be undone.';
    confirmDangerModal(message, selected.identity, function() {
      deleting = true;
      fetch(selected.url + '/server/delete', newPostRequest())
        .then(function(response) { if (!response.ok) throw new Error('Status: ' + response.status); })
        .catch(function(error) { notifyError('Failed to delete ' + selected.identity); })
        .finally(function() { deleting = false; });
    });
  }

  onMount(function() {
    fetch('/instances', newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        Object.keys(json).forEach(function(key) {
          instances = [...instances, { identity: key, running: json[key].running,
                                       module: json[key].module, url: json[key].url }];
        });
        subs.start('/instances/subscribe', function(data) {
          if (data.event === 'running') {
            instances = instances.map(function(value) {
              if (value.identity != data.instance) return value;
              return { identity: value.identity, running: data.running, module: value.module, url: value.url };
            });
          } else if (data.event === 'created') {
            data.instance.url = '/instances/' + data.instance.identity;
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
        {#each instances as instance, index}
          <tr>
            <td class="word-break-all notranslate">
              <i class="fa {instance.running ? 'fa-play play' : 'fa-stop stop'} fa-xl"></i>
              {instance.identity}
            </td>
            <td class="word-break-all notranslate">{instance.module}</td>
            <td class="word-break-all">
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
  .play {
    width: 1em;
    color: #48C78E;
  }

  .stop {
    width: 1em;
    /* color: #F14668; */
  }

  .fa-folder-open {
    width: 1.5em;
  }
</style>
