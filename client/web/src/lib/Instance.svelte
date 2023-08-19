<script>
  import { onMount, getContext } from 'svelte';
  import { goto } from '$app/navigation';

  const instance = getContext('instance');
</script>


<div class="columns is-centered">
  <div class="column is-three-quarters">
    <h1 class="title is-3">{instance.identity()} &nbsp;<i class="fa fa-cube"></i>&nbsp; {instance.module()}</h1>
  </div>
</div>

<slot />
