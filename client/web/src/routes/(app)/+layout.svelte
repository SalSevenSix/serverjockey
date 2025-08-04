<script>
  import 'bulma/css/bulma.min.css';
  import '@fortawesome/fontawesome-free/css/fontawesome.min.css';
  import '@fortawesome/fontawesome-free/css/solid.min.css';
  import '@fortawesome/fontawesome-free/css/brands.min.css';
  import '$lib/layout/styles.css';
  import '$lib/layout/dark.css';

  import { onMount } from 'svelte';
  import { openModal, Modals } from 'svelte-modals';
  import { securityToken } from '$lib/util/sjgmsapi';
  import Notifications from '$lib/layout/Notifications.svelte';
  import LoginModal from '$lib/layout/LoginModal.svelte';
  import Navbar from '$lib/layout/Navbar.svelte';
  import Footer from '$lib/layout/Footer.svelte';

  onMount(function() {
    if ($securityToken) return;
    openModal(LoginModal);
  });
</script>


<svelte:head>
  <title>ServerJockey</title>
</svelte:head>

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
