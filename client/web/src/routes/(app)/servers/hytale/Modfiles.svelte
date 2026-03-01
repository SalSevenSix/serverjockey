<script>
  import { surl } from '$lib/util/sjgmsapi';
  import FileCollection from '$lib/instance/FileCollection.svelte';
  import ConfigFile from '$lib/instance/ConfigFile.svelte';
</script>


<div class="content">
  <p>Only .jar or .zip files accepted.
     All mod files present will automatically be loaded when server starts.</p>
</div>

<FileCollection path="/mod/files" allowDelete={1} filenameHelp="Only .jar and .zip files are accepted."
                validateFilename={function(fn) { return (fn.endsWith('.jar') || fn.endsWith('.zip')); }} />

<div class="block"></div>

<ConfigFile name="Auto Download Mods" path="/config/mods">
  <p>Configure mod list to automatically download latest version when server starts. See the
     <a href={surl('/guides/servers/hytale#automaticModDownloads')}>Hytale help page</a>
     for more information.</p>
</ConfigFile>
