<script>
  import InstanceList from '$lib/instances/InstanceList.svelte';
  import CreateInstance from '$lib/instances/CreateInstance.svelte';
</script>


<div class="columns">
  <div class="column is-two-thirds">
    <InstanceList />
  </div>
  <div class="column is-one-third">
    <CreateInstance />
    <div class="block big-margin-bottom"></div>
  </div>
</div>


<style>
  .big-margin-bottom {
    margin-bottom: 40px;
  }
</style>
