'use strict';

// SETUP

function infoLogger(text) {
  console.log(new Date().getTime() + ' ' + text);
}

infoLogger('*** START ServerLink Bot ***');
var systemrunning = false;
const config = { ...require(process.argv[2]), ...require(process.argv[3]) };
const fs = require('fs');
const fetch = require('node-fetch');
const { Client, Intents } = require('discord.js');
const client = new Client({ intents: ['GUILDS', 'GUILD_MESSAGES', 'DIRECT_MESSAGES'], partials: ['CHANNEL'] });


// UTILS

function errorLogger(error) {
  if (error == null) return null;
  console.error(error);
  return null;
}

function errorHandler(error, message) {
  errorLogger(error);
  message.react('⛔');
}

function sleep(millis) {
  return new Promise(function(resolve) { setTimeout(resolve, millis); });
}

function isEmptyObject(value) {
  if (value == null) return false;
  return (typeof value === 'object' && value.constructor === Object && Object.keys(value).length === 0);
}

function stringToBase10(string) {
  var utf8 = unescape(encodeURIComponent(string));
  var result = '';
  for (var i = 0; i < utf8.length; i++) {
    result += utf8.charCodeAt(i).toString().padStart(3, '0');
  }
  return result;
}

function base10ToString(number) {
  var character;
  var result = '';
  for (var i = 0; i < number.length; i += 3) {
    character = parseInt(number.substr(i, 3), 10).toString(16);
    result += '%' + ((character.length % 2 == 0) ? character : '0' + character);
  }
  return decodeURIComponent(result);
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

function shutdownSystem(source = 'UNKNOWN') {
  systemrunning = false;
  infoLogger('*** END ServerLink Bot (' + source + ') ***');
  client.destroy();
}


// WEBSERVICE CLIENT

async function pollSubscription(url, dataHandler) {
  var polling = (url != null);
  while (systemrunning && polling) {
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
        if (isEmptyObject(data)) return true;
        dataHandler(data);
        return true;
      })
      .catch(function(error) {
        errorLogger(error);
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
      errorHandler(error, message);
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
      fstream.on('error', errorLogger);
      pollSubscription(json.url, function(data) {
        fstream.write(data);
        fstream.write('\n');
      }).then(function() {
          fstream.end();
          message.reactions.removeAll()
            .then(function() { message.react('✅'); })
            .catch(errorLogger);
          message.channel.send({ files: [{ attachment: fpath, name: fname }] })
            .then(function() { fs.unlink(fpath, errorLogger); });
        });
    })
    .catch(function(error) {
      errorHandler(error, message);
    })
    .finally(function() {
      if (message.content === '!shutdown') {
        shutdownSystem('SHUTDOWN');
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
      .catch(function(error) { errorHandler(error, message); });
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
    var name = stringToBase10(data.shift());
    var command = data.shift();
    var body = null;
    if (data.length > 0) {
      if (command === 'set-access-level') {
        body = { level: data[0] };
      } else if (command === 'tele-to') {
        body = { toplayer: stringToBase10(data[0]) };
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
      body = { player: stringToBase10(data[0]), password: data[1] };
      doPostJson(message, '/whitelist/add', body);
    } else if (command === 'remove-name') {
      body = { player: stringToBase10(data[0]) };
      doPostJson(message, '/whitelist/remove', body);
    } else if (command === 'add-id') {
      client.users.fetch(data[0], true, true)
        .then(function(user) {
          var pwd = Math.random().toString(16).substr(2, 8);
          name = user.tag.replace(/ /g, '').replace('#', '');
          infoLogger('Add user: ' + data[0] + ' ' + name);
          body = { player: stringToBase10(name), password: pwd };
          if (doPostJson(message, '/whitelist/add', body)) {
            var text = 'Welcome to the New Hope PZ server.\n';
            text += 'You have been added to the server whitelist.\n';
            text += 'User: ' + name + ' Pass: ' + pwd;
            text += '\nPlease see the #servers channel for information';
            text += ' about how to connect to the server.';
            user.send(text);
          }
        }).catch(function(error) { errorHandler(error, message); });
    } else if (command === 'remove-id') {
      client.users.fetch(data[0], true, true)
        .then(function(user) {
          name = user.tag.replace(/ /g, '').replace('#', '');
          infoLogger('Remove user: ' + data[0] + ' ' + name);
          body = { player: stringToBase10(name) };
          doPostJson(message, '/whitelist/remove', body);
        }).catch(function(error) { errorHandler(error, message); });
    }
  },

  banlist: function(message, data) {
    if (data.length < 2) return;
    var command = data.shift() + '-id';
    var body = { steamid: data.shift() };
    doPostJson(message, '/banlist/' + command, body);
  },

  help: function(message, data) {
    var msg = 'No more help available.';
    if (data.length === 0) {
      msg = '```';
      msg += '!help {command} {action}   : Show help\n';
      msg += '!server                    : Server status\n';
      msg += '!server start              : Start server\n';
      msg += '!server restart            : Save world and restart server\n';
      msg += '!server stop               : Save world and stop server\n';
      msg += '!config                    : Show configuration file URLs\n';
      msg += '!log                       : Show log file URL\n';
      msg += '!world save                : Save the game world\n';
      msg += '!world broadcast {message} : Broadcast message to all players\n';
      msg += '!world chopper             : Trigger chopper event\n';
      msg += '!world gunshot             : Trigger gunshot event\n';
      msg += '!world start-storm         : Start a storm\n';
      msg += '!world stop-weather        : Stop current weather\n';
      msg += '!world start-rain          : Start rain\n';
      msg += '!world stop-rain           : Stop rain\n';
      msg += '```';
      message.channel.send(msg);
      msg = '```';
      msg += '!players                   : Show players currently online\n';
      msg += '!player "{name}" kick      : Kick from server\n';
      msg += '!player "{name}" set-access-level {level} : Set access level\n';
      msg += '!player "{name}" tele-to "{toplayer}"     : Teleport to player\n';
      msg += '!player "{name}" tele-at {x,y,z}          : Teleport to location\n';
      msg += '!player "{name}" give-xp {skill} {xp}     : Give XP\n';
      msg += '!player "{name}" give-item {module} {item} {count} : Give item\n';
      msg += '!player "{name}" spawn-vehicle {module} {item} : Spawn vehicle\n';
      msg += '!player "{name}" spawn-horde {count}      : Spawn zombies\n';
      msg += '!player "{name}" lightning           : Trigger lightning\n';
      msg += '!player "{name}" thunder             : Trigger thunder\n';
      msg += '!whitelist add-name "{name}" "{pwd}" : Add player by name\n';
      msg += '!whitelist remove-name "{name}"      : Remove player by name\n';
      msg += '!whitelist add-id {discordid}        : Add player by discord id\n';
      msg += '!whitelist remove-id {discordid}     : Remove player by discord id\n';
      msg += '!banlist add {steamid}     : Add player SteamID to banlist\n';
      msg += '!banlist remove {steamid}  : Remove player SteamID from banlist\n';
      msg += '```';
      message.channel.send(msg);
      msg = '```';
      msg += '!setconfig ini             : Update INI using attached file\n';
      msg += '!setconfig sandbox         : Update Sandbox using attached file\n';
      msg += '!setconfig spawnregions    : Update Spawnregions using attached file\n';
      msg += '!setconfig jvm             : Update JVM json using attached file\n';
      msg += '!deployment backup-world        : Backup game world to zip file\n';
      msg += '!deployment wipe-world-all      : Delete game world folder\n';
      msg += '!deployment wipe-world-playerdb : Delete only player DB\n';
      msg += '!deployment wipe-world-config   : Delete only config files\n';
      msg += '!deployment wipe-world-save     : Delete only map files\n';
      msg += '!deployment install-runtime {beta} : Install game server\n';
      msg += '!shutdown                  : Shutdown server management system\n';
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


// PLAYER EVENTS

async function playerEventHook(channel) {
  var url = null;
  while (systemrunning) {
    while (systemrunning && url == null) {
      url = await fetch(config.SERVER_URL + '/players/subscribe', newPostRequest('application/json'))
        .then(function(response) {
          if (!response.ok) throw new Error('Status: ' + response.status);
          return response.json();
        })
        .then(function(json) {
          infoLogger('Subscribed to player events at ' + json.url);
          return json.url;
        })
        .catch(errorLogger);
      if (systemrunning && url == null) {
        await sleep(12000);
      }
    }
    if (systemrunning && url != null) {
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


// DISCORD HOOKS

client.on('messageCreate', function(message) {
  //if (message.author.bot) return;
  if (!message.content.startsWith('!')) return;
  var data = parse(message.content);
  var command = data.shift().toLowerCase();
  if (!handlers.hasOwnProperty(command)) return;
  infoLogger(message.member.user.tag + ' ' + message.content)
  handlers[command](message, data);
});

client.once('ready', function() {
  systemrunning = true;
  infoLogger('Logged in as ' + client.user.tag);
  client.channels.fetch(config.EVENTS_CHANNEL_ID)
    .then(function(channel) {
      infoLogger('Publishing events to ' + channel);
      playerEventHook(channel);   // fork
      if (config.hasOwnProperty('STARTUP_REPORT')) {
        fs.promises.access(config.STARTUP_REPORT, fs.constants.F_OK)
          .then(function() {
            infoLogger('Sending startup report.');
            channel.send({
              content: '**Startup Report**',
              files: [{ attachment: config.STARTUP_REPORT, name: 'report.text' }] });
          })
          .catch(function() { infoLogger('No startup report found.'); });
      }
    })
    .catch(errorLogger);
});


// SHUTDOWN HOOK

process.on('SIGTERM', function() {
  shutdownSystem('SIGTERM');
});


// MAIN

infoLogger('Initialised with config...');
console.log(config);
client.login(config.BOT_TOKEN);
