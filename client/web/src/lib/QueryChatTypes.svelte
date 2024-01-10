<script>
  import { getContext } from 'svelte';

  const query = getContext('query');

  let type = 'both';

  query.criteria.chat = function() {
    return { type: type };
  }
</script>


<div class="content">
  <p class="has-text-weight-bold">Include</p>
  <div class="field">
    <div class="control">
      <label class="radio m-1 p-2">
        <input type="radio" name="chat" value="chat" bind:group={type}>&nbsp; Chat
      </label>
      <label class="radio m-1 p-2">
        <input type="radio" name="session" value="session" bind:group={type}>&nbsp; Session
      </label>
      <label class="radio m-1 p-2">
        <input type="radio" name="both" value="both" bind:group={type}>&nbsp; Both
      </label>
    </div>
  </div>
</div>


<style>
  .radio {
    background-color: white;
    border: 2px;
    border-style: solid;
    border-color: #DBDBDB;
    border-radius: 5px;
    width: 110px;
  }
</style>
