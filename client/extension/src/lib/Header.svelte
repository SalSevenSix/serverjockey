<script>
  import { fly } from 'svelte/transition';
  import { errorText } from '$lib/sjgmsapi';
</script>


{#if $errorText}
  <div in:fly={{ duration: 300, y: -300 }} class="error-container"><div>
    <p><span class="error-header">[ERROR]</span>
      {$errorText}
    </p>
  </div></div>
{/if}

<div class="header-container">
  <h1>Modz Helper</h1>
</div>


<style>
  .error-container {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    z-index: 20;
    background-color: rgba(22, 32, 45, 0.9);
    backdrop-filter: blur(3px);
  }

  .error-container > div {
    margin: 32px 16px;
    font-size: 1.1em;
    color: #EBEBEB;
  }

  .error-header {
    font-weight: bold;
    color: red;
  }

  .header-container h1 {
    margin: 8px 0;
    letter-spacing: 0.1em;
  }
</style>
