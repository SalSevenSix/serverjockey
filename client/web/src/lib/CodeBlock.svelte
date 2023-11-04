<script>
  let codeElement;

  function copyToClipboard() {
    if (!codeElement) return;
    navigator.clipboard.writeText(codeElement.textContent.trim());
  }
</script>


<pre bind:this={codeElement} class="pre is-thinner"><slot /><button
  title="Copy" class="button is-dark" on:click={copyToClipboard}>
  <i class="fa fa-copy fa-xl"></i>
</button></pre>


<style>
  .pre {
    position: relative;
  }

  .button {
    position: absolute;
    top: 0.4em;
    right: 0.8em;
    width: 3em;
  }
</style>
