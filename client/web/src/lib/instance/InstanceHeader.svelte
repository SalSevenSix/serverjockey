<script>
  import { getContext } from 'svelte';

  const instance = getContext('instance');
</script>


<div class="columns is-centered">
  <div class="column is-three-quarters">
    <h1 id="instanceHeader" class="title is-3 notranslate">
      {instance.identity()} &nbsp;<i class="fa fa-cube"></i>&nbsp; {instance.module()}
    </h1>
  </div>
</div>
