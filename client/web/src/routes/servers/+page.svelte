<script>
  import InstanceList from '$lib/InstanceList.svelte';
  import CreateInstance from '$lib/CreateInstance.svelte';
</script>


<div class="columns">
  <div class="column is-two-thirds">
    <InstanceList />
    <div class="block"></div>
  </div>
  <div class="column is-one-third">
    <CreateInstance />
    <div class="block big-margin-bottom"></div>
  </div>
</div>


<style>
  .big-margin-bottom {
    margin-bottom: 160px;
  }
</style>
