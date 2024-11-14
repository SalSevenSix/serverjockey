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
