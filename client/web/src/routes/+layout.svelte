<script>
  import 'bulma/css/bulma.min.css';
  import '@fortawesome/fontawesome-free/css/fontawesome.min.css';
  import '@fortawesome/fontawesome-free/css/solid.min.css';
  import '@fortawesome/fontawesome-free/css/brands.min.css';
  import './styles.css';
  import './dark.css';

  import { onMount } from 'svelte';
  import { Modals } from 'svelte-modals';
  import { loginModal } from '$lib/modals';
  import { securityToken } from '$lib/sjgmsapi';

  import Navbar from '$lib/Navbar.svelte';
  import Notifications from '$lib/Notifications.svelte';
  import Footer from '$lib/Footer.svelte';

  onMount(function() {
    if ($securityToken) return;
    loginModal();
  });
</script>


<section class="section">
  <div class="container">
    {#if $securityToken}
      <Navbar />
      <slot />
      <Footer />
    {/if}
  </div>
</section>

<Notifications />

<Modals>
  <div slot="backdrop" />
</Modals>
