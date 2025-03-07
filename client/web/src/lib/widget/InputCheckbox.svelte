<script>
  export let id;
  export let label;
  export let checked = false;
</script>


<div class="field">
  <div class="control">
    <label class="checkbox">
      <input id={id} type="checkbox" bind:checked={checked}>&nbsp; {label}
    </label>
  </div>
</div>
