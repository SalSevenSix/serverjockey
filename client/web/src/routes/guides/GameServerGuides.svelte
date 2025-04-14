<script>
  import { onMount } from 'svelte';
  import { surl, newGetRequest } from '$lib/util/sjgmsapi';
  import { notifyError } from '$lib/util/notifications';
  import SpinnerIcon from '$lib/widget/SpinnerIcon.svelte';

  let loading = true;
  let modules = null;

  onMount(function() {
    fetch(surl('/modules'), newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) { modules = json; })
      .catch(function() { notifyError('Failed to load module list.'); })
      .finally(function() { loading = false; });
  });
</script>


{#if modules}
  <div class="columns is-multiline">
    {#each Object.keys(modules) as module}
      <div class="column is-one-quarter-desktop is-one-third-tablet">
        <a id="gameServerGuidesM{module}" title="{modules[module]} guide" href={surl('/guides/servers/' + module)}>
          <div class="card">
            <header class="card-header card-header-title notranslate">{modules[module]}</header>
            <div class="card-image">
              <figure class="image">
                <img src={surl('/assets/games/' + module + '-tile.jpg')} alt="{modules[module]} icon" />
              </figure>
            </div>
          </div>
        </a>
      </div>
    {/each}
  </div>
{:else}
  <div class="content">
    <p>
      {#if loading}
        <SpinnerIcon /> loading...
      {:else}
        <i class="fa fa-triangle-exclamation fa-lg"></i>&nbsp; Error loading game server guides
      {/if}
    </p>
  </div>
{/if}


<style>
  .card {
    background-color: #F5F5F5;
    color: #485fC7;
    max-width: 400px;
    margin-left: auto;
    margin-right: auto;
  }

  .card:hover {
    color: var(--color-standard-darker-bwg);
  }

  .card-header-title {
    color: inherit;
  }
</style>
