<script>
  export let id;
  export let name;
  export let value;

  export let title = null;
  export let onKeypress = null;
  export let disabled = false;
  export let autofocus = false;
</script>


<div class="field">
  <label for={id} class="label" title={title}>{name}</label>
  <div class="control">
    <!-- svelte-ignore a11y-autofocus -->
    <input id={id} type="password" class="input" bind:value={value}
           on:keypress={onKeypress} disabled={disabled} autofocus={autofocus}>
  </div>
</div>
