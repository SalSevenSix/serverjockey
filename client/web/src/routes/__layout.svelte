<script>
  import 'bulma/css/bulma.css';
  import 'font-awesome5/css/fontawesome.css';
  import 'font-awesome5/css/fa-regular.css';
	import '../app.css';

  import Navbar from '$lib/Navbar.svelte';
	import { Modals } from 'svelte-modals';
  import Notifications from '$lib/Notifications.svelte';
</script>

<section class="section">
  <div class="container">
    <Navbar />
    <slot />
  </div>
</section>

<Notifications />

<Modals>
  <div slot="backdrop" />
</Modals>
