<script>
  import { getContext } from 'svelte';
  const instance = getContext('instance');
</script>


<slot {instance} />
