<script>
  import { getContext } from 'svelte';
  import { generateId } from '$lib/util';

  const query = getContext('query');
  const inputId = 'querySearchText' + generateId();

  export let key = 'search';
  export let name = 'Search';
  export let title = null;
  export let placeholder = null;

  let text = '';

  function kpExecute(event) {
    if (event.key === 'Enter') { query.execute(); }
  }

  query.criteria[key] = function() {
    return { text: text };
  }
</script>


<div class="block">
  <div class="field">
    <label class="label" for={inputId} title={title}>{name}</label>
    <div class="control">
      <input id={inputId} class="input" type="text" placeholder={placeholder}
             on:keypress={kpExecute} bind:value={text}>
    </div>
  </div>
</div>
