<script>
  import { slide } from 'svelte/transition';
  import { quadInOut } from 'svelte/easing';

  export let open = false;
  export let icon = null;
  export let notranslate = false;
  export let title;

  let visible = open;

  function toggle() {
    visible = !visible;
  }
</script>


<hr />
<div class="columns is-mobile mb-0">
  <div class="column is-three-quarters">
    <h2 class="title is-5" class:notranslate={notranslate}>
      {#if icon}<i class="fa {icon} fa-lg"></i>{/if}{title}
    </h2>
  </div>
  <div class="column is-one-quarter">
    <div class="buttons is-right">
      <button class="button is-dark" on:click={toggle} title={visible ? 'HIDE' : 'SHOW'}>
        <i class="fa {visible ? 'fa-caret-down' : 'fa-caret-left'} fa-2x"></i>
      </button>
    </div>
  </div>
</div>

{#if visible}
  <div transition:slide={{ duration: 100, easing: quadInOut }}>
    <slot />
  </div>
{/if}


<style>
  h2 i {
    width: 1.45em;
  }

  button i {
    width: 0.9em;
  }
</style>
