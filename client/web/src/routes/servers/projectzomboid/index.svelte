<script>
  import Instance from '$lib/Instance.svelte';
  import Collapsible from '$lib/Collapsible.svelte';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
  import Players from '$lib/Players.svelte';
  import ConsoleLog from '$lib/ConsoleLog.svelte';
  import FileSystem from '$lib/FileSystem.svelte';
  import ConfigFile from '$lib/ConfigFile.svelte';
  import InstallRuntime from '$lib/InstallRuntime.svelte';
  import DeploymentActions from '$lib/DeploymentActions.svelte';
  import BackupRestoreActions from '$lib/BackupRestoreActions.svelte';
  import CommandBuilder from '$lib/CommandBuilder.svelte';

  let deploymentActions = {
    'wipe-world-save': 'Reset the game world save only. This is the map and player characters.',
    'wipe-world-playerdb': 'Reset the player database only. This is logins, whitelist, banlist.',
    'wipe-world-config': 'Reset the configuration files only. INI, Sandbox and Spawn config files.',
    'wipe-world-all': 'Reset all of the above.'
  };

  let consoleCommands = {
    'world': {
      'save': [],
      'broadcast': [
        {input: 'text', type: 'string', name: 'message'}
      ],
      'chopper': [],
      'gunshot': [],
      'start-storm': [],
      'stop-weather': [],
      'start-rain': [],
      'stop-rain': []
    },
    'players': {
      'kick': [
        {input: 'text', type: 'item', name: 'player'}
      ],
      'set-access-level': [
        {input: 'text', type: 'item', name: 'player'},
        {input: 'radio', type: 'string', name: 'level', options: ['none', 'observer', 'gm', 'overseer', 'moderator', 'admin']}
      ],
      'tele-to': [
        {input: 'text', type: 'item', name: 'player'},
        {input: 'text', type: 'string', name: 'toplayer'}
      ],
      'tele-at': [
        {input: 'text', type: 'item', name: 'player'},
        {input: 'text', type: 'string', name: 'location'}
      ],
      'give-xp': [
        {input: 'text', type: 'item', name: 'player'},
        {input: 'radio', type: 'string', name: 'skill', options: ['Combat', 'Axe', 'Blunt', 'SmallBlunt', 'LongBlade', 'SmallBlade', 'Spear', 'Maintenance', 'Firearm', 'Aiming', 'Reloading', 'Agility', 'Sprinting', 'Lightfoot', 'Nimble', 'Sneak', 'Crafting', 'Woodwork', 'Cooking', 'Farming', 'Doctor', 'Electricity', 'MetalWelding', 'Mechanics', 'Tailoring', 'Survivalist', 'Fishing', 'Trapping', 'PlantScavenging']},
        {input: 'text', type: 'number', name: 'xp'}
      ],
      'give-item': [
        {input: 'text', type: 'item', name: 'player'},
        {input: 'text', type: 'string', name: 'module'},
        {input: 'text', type: 'string', name: 'item'},
        {input: 'text', type: 'number', name: 'count'}
      ],
      'spawn-vehicle': [
        {input: 'text', type: 'item', name: 'player'},
        {input: 'text', type: 'string', name: 'module'},
        {input: 'text', type: 'string', name: 'item'}
      ],
      'spawn-horde': [
        {input: 'text', type: 'item', name: 'player'},
        {input: 'text', type: 'number', name: 'count'}
      ],
      'lightning': [
        {input: 'text', type: 'item', name: 'player'}
      ],
      'thunder': [
        {input: 'text', type: 'item', name: 'player'}
      ]
    },
    'whitelist': {
      'add': [
        {input: 'text', type: 'string', name: 'player'},
        {input: 'text', type: 'string', name: 'password'}
      ],
      'remove': [
        {input: 'text', type: 'string', name: 'player'}
      ]
    },
    'banlist': {
      'add-id': [
        {input: 'text', type: 'string', name: 'steamid'}
      ],
      'remove-id': [
        {input: 'text', type: 'string', name: 'steamid'}
      ]
    }
  };
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
      <Collapsible title="Logging">
        <ConsoleLog hasConsoleLogFile />
        <FileSystem allowDelete />
      </Collapsible>
      <Collapsible title="Console Commands">
        <CommandBuilder commands={consoleCommands} />
      </Collapsible>
      <Collapsible title="Configuration">
        <div class="content">
          <p>For help understanding Project Zomboid configuration files. Please see the
          <a href="https://steamcommunity.com/sharedfiles/filedetails/?id=2682570605" target="_blank">
          excellent guide on Steam</a> by Aiteron.</p>
        </div>
        <ConfigFile name="INI Settings" path="/config/ini" />
        <ConfigFile name="Sandbox Settings" path="/config/sandbox" />
        <ConfigFile name="Spawn Regions" path="/config/spawnregions" />
        <ConfigFile name="Spawn Points" path="/config/spawnpoints" />
        <ConfigFile name="JRE Settings" path="/config/jvm">
          <p>
            Change -Xmx to set the memory available to the server.
            e.g. &quot;-Xmx8g&quot; for 8Gb memory.
            Do not change other fields unless you know what you are doing!
          </p>
        </ConfigFile>
      </Collapsible>
      <Collapsible title="Deployment">
        <InstallRuntime qualifierName="Beta" showLog />
        <DeploymentActions actions={deploymentActions} />
      </Collapsible>
      <Collapsible title="Backups">
        <BackupRestoreActions />
      </Collapsible>
      <hr />
    </div>
  </div>
</Instance>
