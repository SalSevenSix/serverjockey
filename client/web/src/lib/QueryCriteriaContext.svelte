<script>
  import { setContext } from 'svelte';
  import { writable } from 'svelte/store';

  const executes = new Set();

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
    onExecute: function(callable) {
      executes.add(callable);
    },
    execute: function() {
      for (let callable of executes.values()) {
        callable();
      }
    }
  };

  setContext('query', query);
</script>


<slot />
