<script>
  import { surl } from '$lib/util/sjgmsapi';

  export let module;
  export let serverName;
</script>


<div class="columns">
  <div class="column is-one-quarter content mb-0">
    <figure class="image ml-0 mr-0 mt-3 max-400">
      <img src={surl('/assets/games/' + module + '-tile.jpg')} alt="{serverName} icon" />
    </figure>
  </div>
  <div class="column is-three-quarters content">
    <h2 class="title is-3 mt-2 notranslate">{serverName}</h2>
    <slot />
  </div>
</div>
