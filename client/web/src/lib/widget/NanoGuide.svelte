<script>
  import ExtLink from '$lib/widget/ExtLink.svelte';
</script>


{#if $$slots.default}
  Use a text editor such as
  <span class="is-family-monospace notranslate">nano</span>
  <slot />
{/if}

If you are new to Nano here is a
<ExtLink href="https://youtu.be/DLeATFgGM-A">video guide</ExtLink>
and the
<ExtLink href="https://www.nano-editor.org/dist/latest/cheatsheet.html">shortcut cheatsheet</ExtLink>.
