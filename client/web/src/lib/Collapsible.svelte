<script>
  export let title;
  let visible = false;

  function toggle() {
    visible = !visible;
  }
</script>

<hr />
<div class="columns is-mobile">
  <div class="column">
    <h2 class="title is-5">{title}</h2>
  </div>
  <div class="column">
    <div class="buttons is-right">
      <button name="toggler" class="button is-dark" on:click={toggle} title={visible ? 'HIDE' : 'SHOW'}>
        &nbsp;{#if visible}<i class="fa fa-caret-down fa-2x"></i>{:else}<i class="fa fa-caret-left fa-2x"></i>&nbsp;{/if}&nbsp;
      </button>
    </div>
  </div>
</div>
{#if visible}
  <slot />
{/if}
