<script>
  import FileCollection from '$lib/instance/FileCollection.svelte';
</script>


<div class="content"><p>
  Only
  <span class="is-family-monospace notranslate">.pak</span>
  files accepted.
</p></div>

<FileCollection path="/pak" allowDelete={1} filenameHelp="Only .pak files accepted."
                validateFilename={function(fn) { return fn.endsWith('.pak'); }} />
