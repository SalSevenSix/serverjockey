<script>
  import FileCollection from '$lib/instance/FileCollection.svelte';
</script>


<div class="content"><p>
  Only
  <span class="is-family-monospace notranslate">.dll</span>
  files accepted. Unpack the dll file from the plugin package then upload here. Please ensure
  <span class="is-family-monospace notranslate">&quot;bepinex_url&quot;</span>
  in Launch Options has the correct BepInEx version to download.
</p></div>

<FileCollection path="/plugin/files" allowDelete={1} filenameHelp="Only .dll files accepted."
                validateFilename={function(fn) { return fn.endsWith('.dll'); }} />
