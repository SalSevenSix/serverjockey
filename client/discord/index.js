'use strict';

// SETUP
//

console.log('*** START ServerLink Bot ***')
const config = { ...require("./config.json"), ...require(process.argv[2]) };
const fetch = require('node-fetch');
const Discord = require('discord.js');
const client = new Discord.Client();


// UTILS
//

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
	for(var i = 0; i < number.length; i += 3) {
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
    return role.name.toLowerCase() === 'admin';
  });
  return admin != null;
}


// WEBSERVICE CLIENT
//

function headerHandler(response) {
  if (!response.ok) {
    throw new Error('Status: ' + response.status);
  }
  return response.json();
}

function errorHandler(message, error) {
  console.error(error);
  message.react('⛔');
}

function doGet(message, path, tostring) {
  fetch(config.BASE_URL + path)
    .then(headerHandler)
    .then(function(json) { message.channel.send(tostring(json)); })
    .catch(function(error) { errorHandler(message, error); });
}

function doPost(message, path, body = null) {
  if (!isAuthorAdmin(message)) {
    message.react('🔒');
    return;
  }
  var request = {
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'X-Secret': config.WEBSERVICE_TOKEN
    }
  }
  if (body != null) {
    request.body = JSON.stringify(body);
  }
  fetch(config.BASE_URL + path, request)
    .then(headerHandler)
    .then(function(json) {
      if (json.response === 'OK') {
        message.react('✅');
      }
    })
    .catch(function(error) { errorHandler(message, error); })
    .finally(function() {
      if (message.content === '!server shutdown') {
        console.log('*** END ServerLink Bot ***');
        client.destroy();
      }
    });
}


// COMMAND HANDLERS
//
const handlers = {

  server: function(message, data) {
    if (data.length === 1) {
      doPost(message, '/server/' + data[0]);
      return;
    }
    doGet(message, '/server', function(body) {
      var result = '```Server is ';
      if (!body.running) {
        result += 'DOWN```';
        return result;
      }
      result += 'UP\n';
      result += 'State:    ' + body.state + '\n';
      var dtl = body.details;
      if (dtl.hasOwnProperty('version')) { result += 'Version:  ' + dtl.version + '\n'; }
      if (dtl.hasOwnProperty('host')) { result += 'Host:     ' + dtl.host + '\n'; }
      if (dtl.hasOwnProperty('port')) { result += 'Port:     ' + dtl.port + '\n'; }
      if (dtl.hasOwnProperty('steamid')) { result += 'SteamID:  ' + dtl.steamid + '\n'; }
      return result + '```';
    });
  },

  config: function(message, data) {
    var result = config.BASE_URL + '/config/options\n';
    result += config.BASE_URL + '/config/ini\n';
    result += config.BASE_URL + '/config/sandbox\n';
    result += config.BASE_URL + '/config/spawnpoints\n';
    result += config.BASE_URL + '/config/spawnregions\n';
    message.channel.send(result);
  },

  log: function(message, data) {
    message.channel.send(config.BASE_URL + '/log');
  },

  world: function(message, data) {
    if (data.length < 1) return;
    var command = data.shift();
    var body = null;
    if (data.length > 0 && command === 'broadcast') {
      body = { message: data.join(' ') };
    }
    doPost(message, '/world/' + command, body);
  },

  players: function(message, data) {
    doGet(message, '/players', function(body) {
      var result = '```Players currently online: ' + body.length + '\n';
      for (var i = 0; i < body.length; i++) {
        result += body[i].steamid + ' ' + body[i].name + '\n';
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
      } else if (command === 'spawn-horde') {
        body = { count: data[0] };
      } else if (command === 'spawn-vehicle') {
        body = { module: data[0], item: data[1] };
      } else if (command === 'give-item') {
        body = { module: data[0], item: data[1] };
        if (data.length > 2) {
          body.count = data[2]
        }
      }
    }
    doPost(message, '/players/' + name + '/' + command, body);
  },

  whitelist: function(message, data) {
    if (data.length < 1) return;
    var command = data.shift();
    var body = null;
    if (command === 'add') {
      body = { player: stringToBase10(data[0]), password: data[1] };
    } else if (command === 'remove') {
      body = { player: stringToBase10(data[0]) };
    }
    doPost(message, '/whitelist/' + command, body);
  },

  banlist: function(message, data) {
    if (data.length < 2) return;
    var command = data.shift() + '-id';
    var body = { steamid: data.shift() };
    doPost(message, '/banlist/' + command, body);
  },

  help: function(message, data) {
    var result = '```';
    result += '!help                      : Show this command list\n';
    result += '!server                    : Server status\n';
    result += '!server start              : Start server\n';
    result += '!server restart            : Save world and restart server\n';
    result += '!server stop               : Save world and stop server\n';
    result += '!config                    : Show configuration file URLs\n';
    result += '!log                       : Show log file URL\n';
    result += '!world save                : Save the game world\n';
    result += '!world broadcast {message} : Broadcast message to players online\n';
    result += '!world chopper             : Trigger chopper event\n';
    result += '!world gunshot             : Trigger gunshot event\n';
    result += '!world start-rain          : Start rain\n';
    result += '!world stop-rain           : Stop rain\n';
    result += '!players                   : Show players currently online\n';
    result += '!player "{name}" kick      : Kick player from server\n';
    result += '!player "{name}" set-access-level {level} :\n';
    result += '   Set access level for player,\n';
    result += '   level options: admin, moderator, overseer, gm, observer, none\n';
    result += '!player "{name}" whitelist :\n';
    result += '   Add online player to the whitelist\n';
    result += '!player "{name}" give-item {module} {item} {count} :\n';
    result += '   Give item to player, count is optional\n';
    result += '!player "{name}" spawn-vehicle {module} {item} :\n';
    result += '   Spawn vehicle for player\n';
    result += '!player "{name}" spawn-horde {count} :\n';
    result += '   Spawn count zombies for player\n';
    result += '!whitelist add-all              : Add players online to whitelist\n';
    result += '!whitelist add "{name}" "{pwd}" : Register new player in whitelist\n';
    result += '!whitelist remove "{name}"      : Remove player from whitelist\n';
    result += '!banlist add {steamid}          : Add player SteamID to banlist\n';
    result += '!banlist remove {steamid}       : Remove player SteamID from banlist```';
    message.channel.send(result);
  }

}


// DISCORD HOOKS
//

client.on('message', function(message) {
  if (message.author.bot) return;
  if (!message.content.startsWith('!')) return;
  var data = parse(message.content);
  var command = data.shift().toLowerCase();
  if (!handlers.hasOwnProperty(command)) return;
  console.log(message.member.user.tag + ' ' + message.content)
  handlers[command](message, data);
});

client.on('ready', function() {
  console.log('Logged in as ' + client.user.tag);
});

console.log('Initialised with config...')
console.log(config)
client.login(config.BOT_TOKEN);
