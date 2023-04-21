<script>
  import 'bulma/css/bulma.css';
  import 'font-awesome5/css/fontawesome-all.css';
  import '../app.css';

  import { securityToken } from '$lib/serverjockeyapi';
  import { onMount } from 'svelte';
  import { Modals } from 'svelte-modals';
  import { loginModal } from '$lib/modals';
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
