<script>
  import { getContext } from 'svelte';

  const query = getContext('query');

  let type = 'chat';

  query.criteria.chat = function() {
    return { type: type };
  }
</script>


<div class="block">
  <p class="has-text-weight-bold mb-1" title="Choose what results to include">Include</p>
  <div class="field">
    <div class="control">
      <label class="radio m-1 p-2" title="Player chat messages">
        <input type="radio" value="chat" bind:group={type}>&nbsp; Chat</label>
      <label class="radio m-1 p-2" title="Player sessions (Login/Logout events)">
        <input type="radio" value="session" bind:group={type}>&nbsp; Session</label>
      <label class="radio m-1 p-2" title="Both Chat and Session">
        <input type="radio" value="both" bind:group={type}>&nbsp; Both</label>
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
    width: 100px;
  }
</style>
