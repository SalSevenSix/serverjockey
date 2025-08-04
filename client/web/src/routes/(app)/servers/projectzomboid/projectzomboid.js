
export const worldActions = [
  { 'key': 'wipe-world-save', 'name': 'Reset Save',
    'desc': 'Reset the game world save only. This is the map and player characters.' },
  { 'key': 'wipe-world-playerdb', 'name': 'Reset Player DB',
    'desc': 'Reset the player database only. This is logins, whitelist, banlist.' },
  { 'key': 'wipe-world-logs', 'name': 'Delete Logs',
    'desc': 'Delete the log files only.' },
  { 'key': 'wipe-world-lua', 'name': 'Reset Lua',
    'desc': 'Reset lua folder. Often used by mods to store data.' },
  { 'key': 'wipe-world-config', 'name': 'Reset Config',
    'desc': 'Reset the configuration files only. INI, Sandbox and Spawn config files.' },
  { 'key': 'wipe-world-autobackups', 'name': 'Delete Autobackups',
    'desc': 'Delete the automatic server created backups.' },
  { 'key': 'wipe-world-all', 'name': 'Reset All', 'icon': 'fa-explosion',
    'desc': 'Reset all of the above.' }];

export const consoleCommands = {
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
      {input: 'radio', type: 'string', name: 'level', options: [
        'none', 'observer', 'gm', 'overseer', 'moderator', 'admin']}
    ],
    'tele-to': [
      {input: 'text>', type: 'item', name: 'player', label: 'Move Player'},
      {input: 'text', type: 'string', name: 'toplayer', label: 'To Player'}
    ],
    'tele-at': [
      {input: 'text>', type: 'item', name: 'player', label: 'Move Player'},
      {input: 'text', type: 'string', name: 'location', label: 'To Location x,y,z'}
    ],
    'give-xp': [
      {input: 'text>', type: 'item', name: 'player'},
      {input: 'radio', type: 'string', name: 'skill', options: [
        'Sprinting', 'Lightfoot', 'Nimble', 'Sneak', 'Aiming', 'Reloading',
        'Axe', 'SmallBlunt', 'Blunt', 'Spear', 'SmallBlade', 'LongBlade', 'Combat',
        'Woodwork', 'Cooking', 'Farming', 'Doctor', 'Electricity', 'MetalWelding',
        'Tailoring', 'Mechanics', 'FlintKnapping', 'Carving', 'Masonry', 'Pottery',
        'Fishing', 'Trapping', 'PlantScavenging', 'Fitness', 'Strength']},
      {input: 'text', type: 'number', name: 'xp', label: 'XP'}
    ],
    'give-item': [
      {input: 'text>', type: 'item', name: 'player'},
      {input: 'text', type: 'string', name: 'module', defval: 'Base'},
      {input: 'text', type: 'string', name: 'item'},
      {input: 'text', type: 'number', name: 'count'}
    ],
    'spawn-vehicle': [
      {input: 'text>', type: 'item', name: 'player'},
      {input: 'text', type: 'string', name: 'module', defval: 'Base'},
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
      {input: 'text>', type: 'string', name: 'steamid', label: 'Steam ID'}
    ],
    'remove-id': [
      {input: 'text>', type: 'string', name: 'steamid', label: 'Steam ID'}
    ]
  }
};
