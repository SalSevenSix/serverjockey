<script>
  import './styles.css';
  import { onMount } from 'svelte';

  onMount(async function() {
    const compact = new URLSearchParams(window.location.search).get('compact');
    if (compact || compact === '') {
      await import('./compact.css');
    }
  });
</script>


<slot />
