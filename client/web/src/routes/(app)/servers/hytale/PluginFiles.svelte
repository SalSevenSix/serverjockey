<script>
  import FileCollection from '$lib/instance/FileCollection.svelte';
</script>


<div class="content"><p>
  Only
  <span class="is-family-monospace notranslate">.jar</span>
  files accepted. Please ensure...<br />
  <span class="is-family-monospace notranslate">&nbsp;&quot;--accept-early-plugins&quot;: true</span><br />
  in Command Line Args config to allow plugins to automatically load when server starts.
</p></div>

<FileCollection path="/mod/plugins" allowDelete={1} filenameHelp="Only .jar files accepted."
                validateFilename={function(fn) { return fn.endsWith('.jar'); }} />
