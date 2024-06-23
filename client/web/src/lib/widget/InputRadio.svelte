<script>
  import { isString, capitalizeKebabCase } from '$lib/util/util';

  export let name;
  export let group;
  export let options;

  export let width = null;
  export let notranslate = false;

  function optionToObject(option) {
    if (isString(option)) return {value: option};
    return option;
  }
</script>


<div class="field">
  <div class="control">
    {#each options.map(optionToObject) as option}
      <label class="radio" class:notranslate={notranslate} style:width={width} title={option.title}>
        <input type="radio" name={name} value={option.value} bind:group={group}>
          {#if width}&nbsp;{/if}{option.name ? option.name : capitalizeKebabCase(option.value)}</label>
    {/each}
  </div>
</div>
