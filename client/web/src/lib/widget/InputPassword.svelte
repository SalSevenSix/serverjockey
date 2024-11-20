<script>
  export let id;
  export let label;
  export let value;

  export let title = null;
  export let onKeypress = null;
  export let disabled = false;
  export let autofocus = false;
  export let nowrap = false;
</script>


<div class="field">
  <label for={id} class="label" class:white-space-nowrap={nowrap} title={title}>{label}</label>
  <div class="control">
    <!-- svelte-ignore a11y-autofocus -->
    <input id={id} type="password" class="input" autocomplete="off" bind:value={value}
           on:keypress={onKeypress} disabled={disabled} autofocus={autofocus}>
  </div>
</div>
