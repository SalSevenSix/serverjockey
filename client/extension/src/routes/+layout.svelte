<script>
  import './styles.css';

  import Header from '$lib/Header.svelte';
  import Session from '$lib/Session.svelte';
</script>


<Header />
<Session>
  <slot />
</Session>
