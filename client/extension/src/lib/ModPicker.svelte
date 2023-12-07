<script>
  import { getContext } from 'svelte';

  const instance = getContext('instance');
</script>


<div>
  <p>{$instance.identity} {$instance.module}</p>
</div>
