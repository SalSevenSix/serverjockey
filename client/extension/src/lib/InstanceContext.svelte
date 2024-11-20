<script>
  import { onMount, setContext } from 'svelte';
  import { writable } from 'svelte/store';
  import { baseurl, newGetRequest, logError, noStorage } from '$lib/sjgmsapi';

  const identityKey = 'sjgmsExtensionSelectedIdentity';
  const instance = writable(null);
  setContext('instance', instance);

  let loading = true;
  let instances = null;
  let identities = [];
  let identity = null;

  $: disabled = loading || !instances;

  $: updateInstance(identity); function updateInstance(selected) {
    if (!selected) return;
    $instance = { identity: selected, module: instances[selected].module, url: instances[selected].url };
    if (noStorage) return;
    localStorage.setItem(identityKey, selected);
  }

  onMount(function() {
    fetch(baseurl('/instances'), newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        instances = json;
        identities = [];
        Object.keys(instances).forEach(function(key) {
          if (instances[key].module === 'projectzomboid') {
            identities.push(key);
          }
        });
        if (identities.length === 1) { identity = identities[0]; }
        if (noStorage) return;
        let storedIdentity = localStorage.getItem(identityKey);
        if (!storedIdentity) return;
        if (identities.length > 1 && identities.includes(storedIdentity)) {
          identity = storedIdentity;
        } else {
          localStorage.removeItem(identityKey);
        }
      })
      .catch(logError)
      .finally(function() { loading = false; });
  });
</script>


<div>
  <h2>Choose Instance</h2>
  {#if identities.length > 0}
    <select id="instanceContextIdentity" bind:value={identity}>
      {#each identities as option}
        <option>{option}</option>
      {/each}
    </select>
  {:else if !loading}
    <p id="instanceContextNoInstancesFound" class="warning-text">&nbsp; no projectzomboid instances found</p>
  {/if}
</div>

{#if !loading && $instance}
  <slot />
{/if}
