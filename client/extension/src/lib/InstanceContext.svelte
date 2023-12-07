<script>
  import { onMount, setContext } from 'svelte';
  import { writable } from 'svelte/store';
  import { baseurl, newGetRequest } from '$lib/sjgmsapi';

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
  }

  onMount(function() {
    fetch(baseurl('/instances'), newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        let fetched = [];
        Object.keys(json).forEach(function(key) {
          if (json[key].module === 'projectzomboid') {
            fetched.push(key);
          }
        });
        identities = fetched;
        instances = json;
        if (identities.length === 1) { identity = identities[0]; }
      })
      .catch(function(error) {
        console.log(error);
      })
      .finally(function() {
        loading = false;
      });
  });
</script>


<div>
  <label for="selectInstance">Choose Instance</label><br />
  <select id="selectInstance" {disabled} bind:value={identity}>
    {#each identities as option}
      <option>{option}</option>
    {/each}
  </select>
</div>

{#if !loading && $instance}
  <slot />
{/if}
