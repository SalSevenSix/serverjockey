<script>
  import ServerStatusStore from '$lib/ServerStatusStore.svelte';
  import Instance from '$lib/Instance.svelte';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
</script>


<ServerStatusStore><Instance>
  <div class="columns">
    <div class="column">
      <div class="columns">
        <div class="column">
          <ServerControls />
          <ServerStatus />
        </div>
        <div class="column">
          <p>No Players Component yet</p>
        </div>
      </div>
    </div>
  </div>
</Instance></ServerStatusStore>
