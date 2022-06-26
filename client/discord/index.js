'use strict';


class Logger {

  #timestamp() {
    return new Date().getTime().toString() + ' ';
  }

  raw(value) {
    console.log(value);
  }

  info(value) {
    console.log(this.#timestamp() + value);
  }

  error(value) {
    if (value == null) return null;
    console.error(value);
    return null;
  }

  messageError(value, message) {
    console.error(value);
    message.react('⛔');
  }

}


class Utils {

  sleep(millis) {
    return new Promise(function(resolve) { setTimeout(resolve, millis); });
  }

  isEmptyObject(value) {
    if (value == null) return false;
    return (typeof value === 'object' && value.constructor === Object && Object.keys(value).length === 0);
  }

  stringToBase10(string) {
    var utf8 = unescape(encodeURIComponent(string));
    var result = '';
    for (var i = 0; i < utf8.length; i++) {
      result += utf8.charCodeAt(i).toString().padStart(3, '0');
    }
    return result;
  }

  base10ToString(number) {
    var character;
    var result = '';
    for (var i = 0; i < number.length; i += 3) {
      character = parseInt(number.substr(i, 3), 10).toString(16);
      result += '%' + ((character.length % 2 == 0) ? character : '0' + character);
    }
    return decodeURIComponent(result);
  }

}


function parse(message) {
  message = message.slice(1);
  var regexp = /[^\s"]+|"([^"]*)"/gi;
  var result = [];
  do {
    var match = regexp.exec(message);
    if (match != null) {
      result.push(match[1] ? match[1] : match[0]);
    }
  } while (match != null);
  return result;
}

function isAuthorAdmin(message) {
  var admin = message.member.roles.cache.find(function(role) {
    return role.name.toLowerCase() === 'pzadmin';
  });
  return admin != null;
}


// WEBSERVICE CLIENT

async function pollSubscription(url, dataHandler) {
  var polling = (url != null);
  while (running && polling) {
    polling = await fetch(url)
      .then(function(response) {
        if (response.status === 404) return null;
        if (!response.ok) throw new Error('Status: ' + response.status);
        if (response.status === 204) return {};
        var ct = response.headers.get('Content-Type');
        if (ct.startsWith('text/plain')) return response.text();
        return response.json();
      })
      .then(function(data) {
        if (data == null) return false;
        if (util.isEmptyObject(data)) return true;
        dataHandler(data);
        return true;
      })
      .catch(function(error) {
        logger.error(error);
        return false;
      });
  }
}

function newPostRequest(ct) {
  return {
    method: 'post',
    headers: {
      'Content-Type': ct,
      'X-Secret': config.SERVER_TOKEN
    }
  };
}

function doGet(message, path, tostring) {
  fetch(config.SERVER_URL + path)
    .then(function(response) {
      if (!response.ok) throw new Error('Status: ' + response.status);
      return response.json();
    })
    .then(function(json) {
      message.channel.send(tostring(json));
    })
    .catch(function(error) {
      logger.messageError(error, message);
    });
}

function doPost(message, path, request) {
  if (!isAuthorAdmin(message)) {
    message.react('🔒');
    return false;
  }
  var url = config.SERVER_URL + path;
  if (path.startsWith('http')) { url = path; }
  fetch(url, request)
    .then(function(response) {
      if (!response.ok) throw new Error('Status: ' + response.status);
      if (response.status === 204) return null;
      return response.json();
    })
    .then(function(json) {
      if (json == null || !json.url) {
        message.react('✅');
        return;
      }
      message.react('⌛');
      var fname = message.id + '.text';
      var fpath = '/tmp/' + fname;
      var fstream = fs.createWriteStream(fpath);
      fstream.on('error', logger.error);
      pollSubscription(json.url, function(data) {
        fstream.write(data);
        fstream.write('\n');
      }).then(function() {
          fstream.end();
          message.reactions.removeAll()
            .then(function() { message.react('✅'); })
            .catch(logger.error);
          message.channel.send({ files: [{ attachment: fpath, name: fname }] })
            .then(function() { fs.unlink(fpath, logger.error); });
        });
    })
    .catch(function(error) {
      logger.messageError(error, message);
    })
    .finally(function() {
      if (message.content === config.CMD_PREFIX + 'shutdown') {
        shutdown();
      }
    });
  return true;
}

function doPostJson(message, path, body = null) {
  var request = newPostRequest('application/json');
  if (body != null) { request.body = JSON.stringify(body); }
  return doPost(message, path, request);
}

function doPostText(message, path, body) {
  if (body == null) { body = 'null'; }
  body = body.replace(/\r\n/g, '\n');
  var request = newPostRequest('text/plain');
  request.body = body;
  return doPost(message, path, request);
}


// COMMAND HANDLERS

const handlers = {

  shutdown: function(message, data) {
    var baseurl = config.SERVER_URL.split('/', 3).join('/');
    doPostJson(message, baseurl + '/system/shutdown');
  },

  server: function(message, data) {
    if (data.length === 1) {
      doPostJson(message, '/server/' + data[0]);
      return;
    }
    doGet(message, '/server', function(body) {
      var result = '```Server is ';
      if (!body.running) {
        result += 'DOWN```';
        return result;
      }
      result += body.state + '\n';
      var dtl = body.details;
      if (dtl.hasOwnProperty('version')) { result += 'Version:  ' + dtl.version + '\n'; }
      //if (dtl.hasOwnProperty('host')) { result += 'Host:     ' + dtl.host + '\n'; }
      //if (dtl.hasOwnProperty('port')) { result += 'Port:     ' + dtl.port + '\n'; }
      if (dtl.hasOwnProperty('ingametime')) { result += 'Ingame:   ' + dtl.ingametime + '\n'; }
      //if (dtl.hasOwnProperty('steamid')) { result += 'SteamID:  ' + dtl.steamid + '\n'; }
      return result + '```';
    });
  },

  config: function(message, data) {
    var prefix = config.SERVER_URL + '/config/'
    var result = prefix + 'jvm\n';
    result += prefix + 'options\n';
    result += prefix + 'ini\n';
    result += prefix + 'sandbox\n';
    result += prefix + 'spawnpoints\n';
    result += prefix + 'spawnregions\n';
    message.channel.send(result);
  },

  setconfig: function(message, data) {
    if (data.length < 1) return;
    if (message.attachments.length < 1) return;
    var command = data.shift();
    fetch(message.attachments.first().url)
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.text();
      })
      .then(function(body) {
        doPostText(message, '/config/' + command, body);
      })
      .catch(function(error) { logger.messageError(error, message); });
  },

  log: function(message, data) {
    message.channel.send(config.SERVER_URL + '/log');
  },

  world: function(message, data) {
    if (data.length < 1) return;
    var command = data.shift();
    var body = null;
    if (data.length > 0 && command === 'broadcast') {
      body = { message: data.join(' ') };
    }
    doPostJson(message, '/world/' + command, body);
  },

  deployment: function(message, data) {
    if (data.length < 1) return;
    var command = data.shift();
    var body = null;
    if (command === 'install-runtime') {
      body = { wipe: true, validate: true };
      if (data.length > 0) { body.beta = data[0]; }
    }
    doPostJson(message, '/deployment/' + command, body);
  },

  players: function(message, data) {
    doGet(message, '/players', function(body) {
      var result = '```Players currently online: ' + body.length + '\n';
      for (var i = 0; i < body.length; i++) {
        if (body[i].steamid == null) {
          result += 'LOGGING IN        ';
        } else {
          result += body[i].steamid + ' ';
        }
        result += body[i].name + '\n';
      }
      return result + '```';
    });
  },

  player: function(message, data) {
    if (data.length < 2) return;
    var name = util.stringToBase10(data.shift());
    var command = data.shift();
    var body = null;
    if (data.length > 0) {
      if (command === 'set-access-level') {
        body = { level: data[0] };
      } else if (command === 'tele-to') {
        body = { toplayer: util.stringToBase10(data[0]) };
      } else if (command === 'tele-at') {
        body = { location: data[0] };
      } else if (command === 'spawn-horde') {
        body = { count: data[0] };
      } else if (command === 'spawn-vehicle') {
        body = { module: data[0], item: data[1] };
      } else if (command === 'give-xp') {
        body = { skill: data[0], xp: data[1] };
      } else if (command === 'give-item') {
        body = { module: data[0], item: data[1] };
        if (data.length > 2) { body.count = data[2]; }
      }
    }
    doPostJson(message, '/players/' + name + '/' + command, body);
  },

  whitelist: function(message, data) {
    if (data.length < 1) return;
    var command = data.shift();
    var name = null;
    var body = null;
    if (command === 'add-name') {
      body = { player: util.stringToBase10(data[0]), password: data[1] };
      doPostJson(message, '/whitelist/add', body);
    } else if (command === 'remove-name') {
      body = { player: util.stringToBase10(data[0]) };
      doPostJson(message, '/whitelist/remove', body);
    } else if (command === 'add-id') {
      client.users.fetch(data[0], true, true)
        .then(function(user) {
          var pwd = Math.random().toString(16).substr(2, 8);
          name = user.tag.replace(/ /g, '').replace('#', '');
          logger.info('Add user: ' + data[0] + ' ' + name);
          body = { player: util.stringToBase10(name), password: pwd };
          if (doPostJson(message, '/whitelist/add', body)) {
            user.send(config.WHITELIST_DM.replace('${user}', name).replace('${pass}', pwd));
          }
        }).catch(function(error) { logger.messageError(error, message); });
    } else if (command === 'remove-id') {
      client.users.fetch(data[0], true, true)
        .then(function(user) {
          name = user.tag.replace(/ /g, '').replace('#', '');
          logger.info('Remove user: ' + data[0] + ' ' + name);
          body = { player: util.stringToBase10(name) };
          doPostJson(message, '/whitelist/remove', body);
        }).catch(function(error) { logger.messageError(error, message); });
    }
  },

  banlist: function(message, data) {
    if (data.length < 2) return;
    var command = data.shift() + '-id';
    var body = { steamid: data.shift() };
    doPostJson(message, '/banlist/' + command, body);
  },

  help: function(message, data) {
    var pre = config.CMD_PREFIX;
    var msg = 'No more help available.';
    if (data.length === 0) {
      msg = '```';
      msg += pre + 'help {command} {action}   : Show help\n';
      msg += pre + 'server                    : Server status\n';
      msg += pre + 'server start              : Start server\n';
      msg += pre + 'server restart            : Save world and restart server\n';
      msg += pre + 'server stop               : Save world and stop server\n';
      msg += pre + 'config                    : Show configuration file URLs\n';
      msg += pre + 'log                       : Show log file URL\n';
      msg += pre + 'world save                : Save the game world\n';
      msg += pre + 'world broadcast {message} : Broadcast message to all players\n';
      msg += pre + 'world chopper             : Trigger chopper event\n';
      msg += pre + 'world gunshot             : Trigger gunshot event\n';
      msg += pre + 'world start-storm         : Start a storm\n';
      msg += pre + 'world stop-weather        : Stop current weather\n';
      msg += pre + 'world start-rain          : Start rain\n';
      msg += pre + 'world stop-rain           : Stop rain\n';
      msg += '```';
      message.channel.send(msg);
      msg = '```';
      msg += pre + 'players                   : Show players currently online\n';
      msg += pre + 'player "{name}" kick      : Kick from server\n';
      msg += pre + 'player "{name}" set-access-level {level} : Set access level\n';
      msg += pre + 'player "{name}" tele-to "{toplayer}"     : Teleport to player\n';
      msg += pre + 'player "{name}" tele-at {x,y,z}          : Teleport to location\n';
      msg += pre + 'player "{name}" give-xp {skill} {xp}     : Give XP\n';
      msg += pre + 'player "{name}" give-item {module} {item} {count} : Give item\n';
      msg += pre + 'player "{name}" spawn-vehicle {module} {item} : Spawn vehicle\n';
      msg += pre + 'player "{name}" spawn-horde {count}      : Spawn zombies\n';
      msg += pre + 'player "{name}" lightning           : Trigger lightning\n';
      msg += pre + 'player "{name}" thunder             : Trigger thunder\n';
      msg += pre + 'whitelist add-name "{name}" "{pwd}" : Add player by name\n';
      msg += pre + 'whitelist remove-name "{name}"      : Remove player by name\n';
      msg += pre + 'whitelist add-id {discordid}        : Add player by discord id\n';
      msg += pre + 'whitelist remove-id {discordid}     : Remove player by discord id\n';
      msg += pre + 'banlist add {steamid}     : Add player SteamID to banlist\n';
      msg += pre + 'banlist remove {steamid}  : Remove player SteamID from banlist\n';
      msg += '```';
      message.channel.send(msg);
      msg = '```';
      msg += pre + 'setconfig ini             : Update INI using attached file\n';
      msg += pre + 'setconfig sandbox         : Update Sandbox using attached file\n';
      msg += pre + 'setconfig spawnregions    : Update Spawnregions using attached file\n';
      msg += pre + 'setconfig jvm             : Update JVM json using attached file\n';
      msg += pre + 'deployment backup-world        : Backup game world to zip file\n';
      msg += pre + 'deployment wipe-world-all      : Delete game world folder\n';
      msg += pre + 'deployment wipe-world-playerdb : Delete only player DB\n';
      msg += pre + 'deployment wipe-world-config   : Delete only config files\n';
      msg += pre + 'deployment wipe-world-save     : Delete only map files\n';
      msg += pre + 'deployment install-runtime {beta} : Install game server\n';
      msg += pre + 'shutdown                  : Shutdown server management system\n';
      msg += '```';
      message.channel.send(msg);
    } else {
      var query = data.join(' ');
      if (query === 'help') {
        msg = 'Show help text. Use {command} and {action} for more detailed information. Both optional.';
      } else if (query === 'player set-access-level') {
        msg = 'Set access level for online player. Level options:\n';
        msg += '`admin, moderator, overseer, gm, observer, none`';
      } else if (query === 'player give-xp') {
        msg = 'Give XP to online player. Skill options:\n';
        msg += '```Fitness, Strength,\n';
        msg += 'Combat, Axe, Blunt, SmallBlunt, LongBlade, SmallBlade,\n';
        msg += 'Spear, Maintenance, Firearm, Aiming, Reloading,\n';
        msg += 'Agility, Sprinting, Lightfoot, Nimble, Sneak,\n';
        msg += 'Crafting, Woodwork, Cooking, Farming, Doctor,\n';
        msg += 'Electricity, MetalWelding, Mechanics, Tailoring,\n';
        msg += 'Survivalist, Fishing, Trapping, PlantScavenging```';
      } else if (query === 'player give-item') {
        msg = 'Give item to player, {count} is optional.';
      } else if (query === 'player spawn-vehicle') {
        msg = 'Spawn a vehicle next to player. Condition will vary.';
      } else if (query === 'deployment install-runtime') {
        msg = 'Install game server, {beta} optional\n';
        msg += 'Only works on Linux. This process takes time to complete';
      }
      message.channel.send(msg);
    }
  }

}


async function playerEventHook(channel) {
  var url = null;
  while (running) {
    while (running && url == null) {
      url = await fetch(config.SERVER_URL + '/players/subscribe', newPostRequest('application/json'))
        .then(function(response) {
          if (!response.ok) throw new Error('Status: ' + response.status);
          return response.json();
        })
        .then(function(json) {
          logger.info('Subscribed to player events at ' + json.url);
          return json.url;
        })
        .catch(logger.error);
      if (running && url == null) {
        await util.sleep(12000);
      }
    }
    if (running && url != null) {
      await pollSubscription(url, function(json) {
        var result = '';
        if (json.event === 'login') { result += 'LOGIN '; }
        if (json.event === 'logout') { result += 'LOGOUT '; }
        result += json.player.name;
        if (json.player.steamid != null) { result += ' [' + json.player.steamid + ']'; }
        channel.send(result);
      });
    }
    url = null;
  }
}


function startup() {
  running = true;
  logger.info('Logged in as ' + client.user.tag);
  client.channels.fetch(config.EVENTS_CHANNEL_ID)
    .then(function(channel) {
      logger.info('Publishing events to ' + channel);
      playerEventHook(channel);   // fork
      if (config.hasOwnProperty('STARTUP_REPORT')) {
        fs.promises.access(config.STARTUP_REPORT, fs.constants.F_OK)
          .then(function() {
            logger.info('Sending startup report.');
            channel.send({
              content: '**Startup Report**',
              files: [{ attachment: config.STARTUP_REPORT, name: 'report.text' }] });
          })
          .catch(function() { logger.info('No startup report found.'); });
      }
    })
    .catch(logger.error);
}

function handleMessage(message) {
  //if (message.author.bot) return;
  if (!message.content.startsWith(config.CMD_PREFIX)) return;
  var data = parse(message.content);
  var command = data.shift().toLowerCase();
  if (!handlers.hasOwnProperty(command)) return;
  logger.info(message.member.user.tag + ' ' + message.content)
  handlers[command](message, data);
}

function shutdown() {
  running = false;
  logger.info('*** END ServerLink Bot ***');
  client.destroy();
}


// MAIN

var running = false;
const logger = new Logger();
logger.info('*** START ServerLink Bot ***');
const util = new Utils();
const config = { ...require(process.argv[2]), ...require(process.argv[3]) };
const fs = require('fs');
const fetch = require('node-fetch');
const { Client, Intents } = require('discord.js');
const client = new Client({ intents: ['GUILDS', 'GUILD_MESSAGES', 'DIRECT_MESSAGES'], partials: ['CHANNEL'] });
client.once('ready', startup);
client.on('messageCreate', handleMessage);
process.on('SIGTERM', shutdown);
logger.info('Initialised with config...');
logger.raw(config);
client.login(config.BOT_TOKEN);
