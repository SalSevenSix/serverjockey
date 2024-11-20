<script>
  import { setContext, tick } from 'svelte';
  import { writable, get } from 'svelte/store';
  import { generateId } from '$lib/util/util';

  export let contextId = null;

  const executes = {};

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
    contextId: contextId ? contextId : generateId(),
    callups: {},
    criteria: {},
    blocker: newBlockerStore(),
    onExecute: function(key, callable) {
      executes[key] = callable;
    },
    execute: function() {
      tick().then(function() {
        if (get(query.blocker)) return;
        Object.values(executes).forEach(function(callable) {
          callable();
        });
      });
    }
  };

  setContext('query', query);
</script>


<slot />
