<script>
  import 'bulma/css/bulma.css'
	import '../app.css';
  import Navbar from '$lib/Navbar.svelte';
</script>

<section class="section">
  <div class="container">
    <Navbar />
    <slot />
  </div>
</section>
