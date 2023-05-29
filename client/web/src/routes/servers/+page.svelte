<script>
  import InstanceList from '$lib/InstanceList.svelte';
  import CreateInstance from '$lib/CreateInstance.svelte';
</script>


<div class="columns">
  <div class="column is-two-thirds">
    <InstanceList />
  </div>
  <div class="column">
    <CreateInstance />
  </div>
</div>
