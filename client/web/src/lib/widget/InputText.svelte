<script>
  export let id;
  export let name;
  export let value;

  export let title = null;
  export let onKeypress = null;
  export let placeholder = null;
  export let disabled = false;
  export let autofocus = false;
  export let notranslate = false;
  export let nowrap = false;
</script>


<div class="field">
  {#if name}
    <label for={id} class="label" class:white-space-nowrap={nowrap} title={title}>{name}</label>
  {/if}
  <div class="control">
    <!-- svelte-ignore a11y-autofocus -->
    <input id={id} type="text" class="input" class:notranslate={notranslate}
           bind:value={value} on:keypress={onKeypress} placeholder={placeholder}
           disabled={disabled} autofocus={autofocus}>
  </div>
</div>
