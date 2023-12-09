<script>
  import { errorText } from '$lib/sjgmsapi';
</script>


<div>
  {#if $errorText}
    <p class="text-error fixed-height">{$errorText}</p>
  {:else}
    <h1 class="fixed-height">Modz Helper</h1>
  {/if}
</div>


<style>
  .fixed-height {
    margin: 5px 0px 0px 0px;
    height: 22px;
  }
</style>
