<script>
  import Collapsible from '$lib/widget/Collapsible.svelte';
  import ServerStatusStore from '$lib/instance/ServerStatusStore.svelte';
  import InstanceHeader from '$lib/instance/InstanceHeader.svelte';
  import ServerStatus from '$lib/instance/ServerStatus.svelte';
  import ServerConfig from '$lib/instance/ServerConfig.svelte';
  import ServerControls from '$lib/instance/ServerControls.svelte';
  import Players from '$lib/instance/Players.svelte';
  import InstanceLog from '$lib/instance/InstanceLog.svelte';
  import LogFiles from '$lib/instance/LogFiles.svelte';
  import ConfigFile from '$lib/instance/ConfigFile.svelte';
  import RuntimeControls from '$lib/instance/RuntimeControls.svelte';
  import WorldControls from '$lib/instance/WorldControls.svelte';
  import BackupRestoreActions from '$lib/instance/BackupRestoreActions.svelte';
  import CommandBuilder from '$lib/instance/CommandBuilder.svelte';
  import StoreInstance from '$lib/instance/StoreInstance.svelte';
  import Autobackups from './Autobackups.svelte';

  const worldActions = [
    { 'key': 'wipe-world-save', 'name': 'Reset Save',
      'desc': 'Reset the game world save only. This is the map and player characters.' },
    { 'key': 'wipe-world-playerdb', 'name': 'Reset Player DB',
      'desc': 'Reset the player database only. This is logins, whitelist, banlist.' },
    { 'key': 'wipe-world-config', 'name': 'Reset Config',
      'desc': 'Reset the configuration files only. INI, Sandbox and Spawn config files.' },
    { 'key': 'wipe-world-all', 'name': 'Reset All', 'icon': 'fa-explosion',
      'desc': 'Reset all of the above, including logs and auto backups.' }];

  const consoleCommands = {
    'world': {
      'save': [],
      'broadcast': [
        {input: 'text>', type: 'string', name: 'message'}
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
        {input: 'text>', type: 'item', name: 'player'}
      ],
      'set-access-level': [
        {input: 'text>', type: 'item', name: 'player'},
        {input: 'radio', type: 'string', name: 'level', options: ['none', 'observer', 'gm', 'overseer', 'moderator', 'admin']}
      ],
      'tele-to': [
        {input: 'text>', type: 'item', name: 'player'},
        {input: 'text', type: 'string', name: 'toplayer'}
      ],
      'tele-at': [
        {input: 'text>', type: 'item', name: 'player'},
        {input: 'text', type: 'string', name: 'location'}
      ],
      'give-xp': [
        {input: 'text>', type: 'item', name: 'player'},
        {input: 'radio', type: 'string', name: 'skill', options: ['Combat', 'Axe', 'Blunt', 'SmallBlunt', 'LongBlade', 'SmallBlade', 'Spear', 'Maintenance', 'Firearm', 'Aiming', 'Reloading', 'Agility', 'Sprinting', 'Lightfoot', 'Nimble', 'Sneak', 'Crafting', 'Woodwork', 'Cooking', 'Farming', 'Doctor', 'Electricity', 'MetalWelding', 'Mechanics', 'Tailoring', 'Survivalist', 'Fishing', 'Trapping', 'PlantScavenging']},
        {input: 'text', type: 'number', name: 'xp'}
      ],
      'give-item': [
        {input: 'text>', type: 'item', name: 'player'},
        {input: 'text', type: 'string', name: 'module'},
        {input: 'text', type: 'string', name: 'item'},
        {input: 'text', type: 'number', name: 'count'}
      ],
      'spawn-vehicle': [
        {input: 'text>', type: 'item', name: 'player'},
        {input: 'text', type: 'string', name: 'module'},
        {input: 'text', type: 'string', name: 'item'}
      ],
      'spawn-horde': [
        {input: 'text>', type: 'item', name: 'player'},
        {input: 'text', type: 'number', name: 'count'}
      ],
      'lightning': [
        {input: 'text>', type: 'item', name: 'player'}
      ],
      'thunder': [
        {input: 'text>', type: 'item', name: 'player'}
      ]
    },
    'whitelist': {
      'add': [
        {input: 'text>', type: 'string', name: 'player'},
        {input: 'text', type: 'string', name: 'password'}
      ],
      'remove': [
        {input: 'text>', type: 'string', name: 'player'}
      ]
    },
    'banlist': {
      'add-id': [
        {input: 'text>', type: 'string', name: 'steamid'}
      ],
      'remove-id': [
        {input: 'text>', type: 'string', name: 'steamid'}
      ]
    }
  };
</script>


<ServerStatusStore>
  <InstanceHeader />
  <div class="columns">
    <div class="column">
      <div class="columns">
        <div class="column">
          <ServerControls />
          <ServerConfig />
        </div>
        <div class="column">
          <ServerStatus />
        </div>
      </div>
      <InstanceLog canDownload />
      <Collapsible icon="fa-keyboard" title="Console Commands">
        <CommandBuilder commands={consoleCommands} />
      </Collapsible>
      <Collapsible icon="fa-user" title="Players">
        <Players hasSteamId />
      </Collapsible>
      <Collapsible icon="fa-file-code" title="Configuration">
        <div class="content">
          <p>
            For help understanding Project Zomboid configuration files. Please see the
            <a href="https://steamcommunity.com/sharedfiles/filedetails/?id=2682570605" target="_blank">
            excellent guide on Steam <i class="fa fa-up-right-from-square"></i></a> by Aiteron.<br />
            Default configuration files are not generated until after first server start.
          </p>
        </div>
        <ConfigFile name="INI Settings" path="/config/ini" />
        <ConfigFile name="Sandbox Settings" path="/config/sandbox" />
        <ConfigFile name="Spawn Regions" path="/config/spawnregions" />
        <ConfigFile name="Spawn Points" path="/config/spawnpoints" />
        <ConfigFile name="Launch Options" path="/config/cmdargs" />
        <ConfigFile name="JVM Settings" path="/config/jvm">
          <p>
            Change -Xmx to set the memory available to the server.
            e.g. &quot;-Xmx8g&quot; for 8Gb memory.
            Do not change other fields unless you know what you are doing!
          </p>
        </ConfigFile>
      </Collapsible>
      <Collapsible icon="fa-scroll" title="Logging">
        <LogFiles allowDelete={1} />
      </Collapsible>
      <Collapsible icon="fa-gears" title="Deployment">
        <RuntimeControls qualifierName="Beta" />
        <WorldControls actions={worldActions} />
      </Collapsible>
      <Collapsible icon="fa-file-zipper" title="Autobackups">
        <Autobackups />
      </Collapsible>
      <Collapsible icon="fa-box-archive" title="Backups">
        <BackupRestoreActions />
      </Collapsible>
      <StoreInstance />
    </div>
  </div>
</ServerStatusStore>
