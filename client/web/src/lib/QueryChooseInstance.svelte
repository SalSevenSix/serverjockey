<script>
  import { getContext } from 'svelte';

  const query = getContext('query');
  const instance = getContext('instance');

  function getIdentity() {
    if (instance) return instance.identity();
    return null;
  }

  query.criteria.instance = function() {
    return { identity: getIdentity };
  }
</script>


<!-- QueryChooseInstance -->
