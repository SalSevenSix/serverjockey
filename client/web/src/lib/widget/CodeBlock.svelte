<script>
  export let nocopy = false;

  const navigatorClipboard = typeof(navigator) === 'undefined' ? null : navigator.clipboard;

  let codeElement;

  function copyToClipboard() {
    if (!navigatorClipboard || !codeElement) return;
    let text = codeElement.textContent;
    text = text.replace(/\xA0/g, ' ');  // Fix non-breaking whitespace
    navigatorClipboard.writeText(text);
  }
</script>


{#if nocopy || !navigatorClipboard}
  <pre class="pre is-thinner notranslate"><slot /></pre>
{:else}
  <div class="position-relative">
    <pre class="pre is-thinner notranslate" bind:this={codeElement}><slot /></pre>
    <button class="button is-dark" title="COPY" on:click={copyToClipboard}>
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
