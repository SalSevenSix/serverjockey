<script>
  export let id;
  export let label;
  export let value;

  export let title = null;
  export let onKeypress = null;
  export let placeholder = null;
  export let disabled = false;
  export let spellcheck = false;
  export let noautocomplete = false;
  export let autofocus = false;
  export let notranslatelabel = false;
  export let notranslate = false;
  export let nowrap = false;
</script>


<div class="field">
  {#if label}
    <label for={id} class="label" class:white-space-nowrap={nowrap} class:notranslate={notranslatelabel}
           title={title}>{label}</label>
  {/if}
  <div class="control">
    <!-- svelte-ignore a11y-autofocus -->
    <input id={id} type="text" class="input" class:notranslate={notranslate} bind:value={value}
           on:keypress={onKeypress} placeholder={placeholder} disabled={disabled} spellcheck={spellcheck}
           autocomplete={noautocomplete ? 'off' : 'on'} autofocus={autofocus}>
  </div>
</div>
