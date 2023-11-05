<script>
  export let serverName;
  export let imagePath;
</script>


<div class="columns">
  <div class="column is-one-quarter content mb-0">
    <figure class="image ml-0 mr-0 mt-3 max-400"><img src={imagePath} alt="{serverName} icon" /></figure>
  </div>
  <div class="column is-three-quarters content">
    <h2 class="title is-3 mt-2">{serverName}</h2>
    <slot />
  </div>
</div>
