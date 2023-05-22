<script>
  import 'bulma/css/bulma.min.css';
  import '@fortawesome/fontawesome-free/css/fontawesome.min.css';
  import '@fortawesome/fontawesome-free/css/solid.min.css';
  import '../app.css';

  import { onMount } from 'svelte';
  import { Modals } from 'svelte-modals';
  import { loginModal } from '$lib/modals';
  import { securityToken } from '$lib/serverjockeyapi';
  import Navbar from '$lib/Navbar.svelte';
  import Notifications from '$lib/Notifications.svelte';

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
      <hr />
    {/if}
  </div>
</section>

<Notifications />

<Modals>
  <div slot="backdrop" />
</Modals>
