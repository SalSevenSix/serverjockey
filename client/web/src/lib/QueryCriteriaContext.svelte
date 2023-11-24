<script>
  import { setContext } from 'svelte';
  import { writable } from 'svelte/store';

  function newBlockerStore() {
    const { subscribe, set } = writable(false);
    const blocks = [];
    return {
      subscribe,
      notify: function(id, blocked) {
        if (blocked) {
          if (blocks.includes(id)) return;
          blocks.push(id);
          set(true);
        } else {
          let index = blocks.indexOf(id);
          if (index === -1) return;
          blocks.splice(index, 1);
          if (blocks.length === 0) { set(false); }
        }
      }
    };
  }

  const query = {
    criteria: {},
    blocker: newBlockerStore(),
    execute: function() {}
  };

  setContext('query', query);
</script>


<slot />
