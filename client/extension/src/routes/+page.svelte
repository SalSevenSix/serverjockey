<script>
  import { baseurl, newGetRequest } from '$lib/sjgmsapi';

  let url;

  async function getUrl() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    url = tab.url;
  }

  function check() {
    fetch(baseurl('/modules'), newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(data) {
        alert(JSON.stringify(data));
      })
      .catch(function(error) {
        console.log(error);
      });
  }
</script>


<button on:click={getUrl}>Show URL</button>
{#if url}
  <div>Current URL: {url}</div>
{/if}
<br />
<button on:click={check}>Check</button>
