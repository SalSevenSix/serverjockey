<script>
  export let id;
  export let label;
  export let value;

  export let title = null;
  export let disabled = false;
</script>


<div class="field">
  <label for={id} class="label" title={title}>{label}</label>
  <div class="control">
    <textarea id={id} class="textarea" bind:value={value} disabled={disabled}></textarea>
  </div>
</div>
