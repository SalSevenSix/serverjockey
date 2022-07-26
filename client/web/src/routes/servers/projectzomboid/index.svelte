<script>
  import Instance from '$lib/Instance.svelte';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
  import Players from '$lib/Players.svelte';
  import ConsoleLog from '$lib/ConsoleLog.svelte';
  import FileSystem from '$lib/FileSystem.svelte';
  import ConfigFile from '$lib/ConfigFile.svelte';
</script>


<Instance>
  <div class="columns">
    <div class="column">
      <div class="columns">
        <div class="column">
          <ServerControls />
          <ServerStatus />
        </div>
        <div class="column">
          <Players />
        </div>
      </div>
      <hr />
      <ConsoleLog />
      <FileSystem />
      <hr />
      <ConfigFile name="INI Settings" path="/config/ini" />
      <ConfigFile name="Sandbox Settings" path="/config/sandbox" />
      <ConfigFile name="Spawn Regions" path="/config/spawnregions" />
      <ConfigFile name="Spawn Points" path="/config/spawnpoints" />
      <ConfigFile name="JRE Settings" path="/config/jvm" />
      <hr />
    </div>
  </div>
</Instance>
