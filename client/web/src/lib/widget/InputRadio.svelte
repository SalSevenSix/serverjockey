<script>
  import { isString } from 'common/util/util';
  import { capitalizeKebabCase, toCamelCase } from '$lib/util/util';

  export let id;
  export let name;
  export let group;
  export let options;

  export let width = null;
  export let notranslate = false;

  function optionToObject(option) {
    const result = isString(option) ? {value: option} : option;
    result.label = result.name ? result.name : capitalizeKebabCase(result.value);
    result.id = id + toCamelCase(result.label);
    return result;
  }
</script>


<div class="field">
  <div id={id} class="control">
    {#each options.map(optionToObject) as option}
      <label class="radio" class:notranslate={notranslate} style:width={width} title={option.title}>
        <input id={option.id} type="radio" name={name} value={option.value} bind:group={group}>
          {#if width}&nbsp;{/if}{option.label}</label>
    {/each}
  </div>
</div>
