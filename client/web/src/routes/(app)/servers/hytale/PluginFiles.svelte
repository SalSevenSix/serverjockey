<script>
  import FileCollection from '$lib/instance/FileCollection.svelte';
</script>


<div class="content">
  <p>Only .jar files accepted. All plugins present will automatically be loaded when server starts.</p>
</div>

<FileCollection path="/mod/plugins" allowDelete={1} filenameHelp="Only .jar files accepted."
                validateFilename={function(fn) { return fn.endsWith('.jar'); }} />
