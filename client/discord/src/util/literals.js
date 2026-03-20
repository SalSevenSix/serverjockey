export const emojis = {
  unknown: '❓',
  bang: '❗',
  nohelp: '🤷',
  wait: '⌛',
  lock: '🔒',
  error: '⛔',
  success: '✅',
  say: '💬',
  link: '🔗',
  thinking: '🤔',
  medal: '🏅',
  thumbsup: '👍',
  thumbsdown: '👎',
  whitesqr: '⬜',
  greenheart: '💚',
  greendot: '🟢',
  reddot: '🔴',
  skull: '💀',
  restart: '🔄',
  satellite: '📡',
  joystick: '🕹️',
  compass: '🧭',
  dart: '🎯',
  bell: '🔔',
  robot: '🤖',
  avatars: ['🧑', '👩', '👨', '👱', '🧔', '🤠', '👽', '🕵️', '🧙‍♂️', '🧙‍♀️', '🧙', '👨‍🦳', '👩‍🦳', '👨‍🦰', '👩‍🦰',
    '🧝', '🧝‍♂️', '🧝‍♀️', '👵', '👨‍✈️', '👩‍✈️', '🐶', '🐱', '😎', '🤵', '🤵‍♂️', '🤵‍♀️', '👷', '👷‍♂️', '👷‍♀️']
};

export const colourCodes = { light: 0xfffff0, dark: 0x202020, success: 0x48c78e, warning: 0xffe08a, error: 0xf14668 };

export const assetUrls = { sjgmsIconMedium: 'https://serverjockey.net/assets/mediakit/icon-128.png' };

export const startupEvents = { server: 'SERVER', players: 'PLAYERS' };

export const serverAutoDesc = ['Off', 'Auto Start', 'Auto Restart', 'Auto Start and Restart'];

export const serverStates = {
  ready: 'READY', maintenance: 'MAINTENANCE',
  start: 'START', starting: 'STARTING', started: 'STARTED',
  stopping: 'STOPPING', stopped: 'STOPPED', exception: 'EXCEPTION'
};

export const serverTimedStates = [serverStates.ready, serverStates.started, serverStates.stopped];

export const serverUpStates = [serverStates.start, serverStates.starting, serverStates.started, serverStates.stopping];

export const serverDownStates = [serverStates.ready, serverStates.stopped, serverStates.exception];

export const serverStateColours = {
  [serverStates.ready]: colourCodes.dark, [serverStates.maintenance]: colourCodes.light,
  [serverStates.start]: colourCodes.warning, [serverStates.starting]: colourCodes.warning,
  [serverStates.started]: colourCodes.success, [serverStates.exception]: colourCodes.error,
  [serverStates.stopping]: colourCodes.warning, [serverStates.stopped]: colourCodes.dark
};

export const serverEventTriggers = {
  [serverStates.started]: 'on-started', [serverStates.stopped]: 'on-stopped', [serverStates.exception]: 'on-stopped'
};

export const serverSignals = {
  start: 'start', stop: 'stop', restart: 'restart', restartImmediately: 'restart-immediately',
  restartWarnings: 'restart-after-warnings', restartEmpty: 'restart-on-empty'
};

export const playerEvents = { login: 'LOGIN', logout: 'LOGOUT', chat: 'CHAT', death: 'DEATH', clear: 'CLEAR' };

export const playerEventEmojis = {
  [playerEvents.login]: emojis.greendot, [playerEvents.logout]: emojis.reddot, [playerEvents.death]: emojis.skull
};

export const playerEventTriggers = {
  [playerEvents.login]: 'on-login', [playerEvents.logout]: 'on-logout', [playerEvents.death]: 'on-death'
};
