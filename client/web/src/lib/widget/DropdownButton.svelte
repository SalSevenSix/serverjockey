<script>
  import { tick } from 'svelte';
  import { sleep, toCamelCase } from '$lib/util/util';

  export let id;
  export let options;
  export let disabled = false;

  let selecting = false;
  let selected = false;
  let isActive = false;

  function onClick() {
    isActive = !isActive;
  }

  function onMouseEnter() {
    selecting = true;
  }

  function onMouseDown() {
    selected = true;
  }

  function onMouseUp() {
    selected = false;
    doInactive();
  }

  function onMouseLeave() {
    if (selected) { tickInactive(); }
    selected = false;
    selecting = false;
  }

  function onBlur() {
    doInactive();
  }

  function doInactive() {
    if (selected) return;
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


<div class="dropdown" class:is-active={isActive && !disabled}>
  <button id={id} class="button is-warning" aria-haspopup="true" aria-controls="{id}Options"
          on:click={onClick} on:blur={onBlur} disabled={disabled}>
    <slot />
    <span class="icon is-small"><i class="fa fa-angle-down" aria-hidden="true"></i></span>
  </button>
  <div id="{id}Options" class="dropdown-menu mt-0 pt-0" role="menu" tabindex="0"
       on:mouseenter={onMouseEnter} on:mouseleave={onMouseLeave}
       on:mousedown={onMouseDown} on:mouseup={onMouseUp}>
    <div class="dropdown-content">
      {#each options as option}
        <a id="{id}Option{toCamelCase(option.label)}" href={'#'} class="dropdown-item"
           on:click|preventDefault={option.onSelect}>{option.label}</a>
      {/each}
    </div>
  </div>
</div>
