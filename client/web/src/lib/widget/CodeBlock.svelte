<script>
  export let nocopy = false;

  const navigatorClipboard = navigator.clipboard;

  let codeElement;

  function copyToClipboard() {
    if (!navigatorClipboard || !codeElement) return;
    navigatorClipboard.writeText(codeElement.textContent);
  }
</script>


{#if nocopy || !navigatorClipboard}
  <pre class="pre is-thinner notranslate"><slot /></pre>
{:else}
  <div class="position-relative">
    <pre class="pre is-thinner notranslate" bind:this={codeElement}><slot /></pre>
    <button title="Copy" class="button is-dark" on:click={copyToClipboard}>
      <i class="fa fa-copy fa-xl"></i>
    </button>
  </div>
{/if}


<style>
  .button {
    position: absolute;
    top: 0.4em;
    right: 2.5em;
    width: 3em;
  }
</style>
