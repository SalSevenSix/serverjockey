<script>
  import { tick } from 'svelte';
  import { sleep, toCamelCase } from '$lib/util/util';

  export let id;
  export let options;
  export let disabled = false;

  let selecting = false;
  let isActive = false;

  function onClick() {
    isActive = !isActive;
  }

  function onMouseEnter() {
    selecting = true;
  }

  function onMouseLeave() {
    selecting = false;
  }

  function onBlur() {
    if (selecting) {
      sleep(200).then(tickInactive);
    } else {
      tickInactive();
    }
  }

  function tickInactive() {
    tick().then(function() { isActive = false; });
  }
</script>


<div class="dropdown mr-2" class:is-active={isActive && !disabled}>
  <div class="dropdown-trigger">
    <button id={id} class="button is-warning" aria-haspopup="true" aria-controls="{id}Options"
            on:click={onClick} on:blur={onBlur} disabled={disabled}>
      <span><slot /></span>
      <span class="icon is-small"><i class="fa fa-angle-down" aria-hidden="true"></i></span>
    </button>
  </div>
  <div id="{id}Options" class="dropdown-menu mt-0 pt-0" role="menu" tabindex="0"
       on:mouseenter={onMouseEnter} on:mouseleave={onMouseLeave}>
    <div class="dropdown-content">
      {#each options as option}
        <a id="{id}Option{toCamelCase(option.label)}" href={'#'} class="dropdown-item"
           on:click|preventDefault={option.onSelect}>{option.label}</a>
      {/each}
    </div>
  </div>
</div>
