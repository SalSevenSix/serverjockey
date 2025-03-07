<script>
  import { getContext } from 'svelte';

  const query = getContext('query');
  const instance = getContext('instance');

  function getIdentity() {
    return instance ? instance.identity() : null;
  }

  query.criteria.instance = function() {
    return { identity: getIdentity };
  };
</script>


<!-- QueryChooseInstance -->
