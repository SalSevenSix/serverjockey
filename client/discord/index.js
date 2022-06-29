'use strict';


class Logger {

  static raw(value) {
    console.log(value);
  }

  static info(value) {
    console.log(new Date().getTime().toString() + ' ' + value);
  }

  static error(value) {
    if (value == null) return null;
    console.error(value);
    return null;
  }

}


class Util {

  static sleep(millis) {
    return new Promise(function(resolve) { setTimeout(resolve, millis); });
  }

  static isString(value) {
    return (value != null && typeof value === 'string');
  }

  static isEmptyObject(value) {
    if (value == null) return false;
    return (typeof value === 'object' && value.constructor === Object && Object.keys(value).length === 0);
  }

  static getFirstKey(value) {
    if (value == null) return null;
    var keys = Object.keys(value);
    if (keys.length === 0) return null;
    return keys[0];
  }

  static prototypeIncludesProperty(prot, prop) {
    return Object.getOwnPropertyNames(prot).includes(prop);
  }

  static commandLineToList(line) {
    var regexp = /[^\s"]+|"([^"]*)"/gi;
    var result = [];
    do {
      var match = regexp.exec(line);
      if (match != null) {
        result.push(match[1] ? match[1] : match[0]);
      }
    } while (match != null);
    return result;
  }

  static stringToBase10(string) {
    var utf8 = unescape(encodeURIComponent(string));
    var result = '';
    for (var i = 0; i < utf8.length; i++) {
      result += utf8.charCodeAt(i).toString().padStart(3, '0');
    }
    return result;
  }

  static base10ToString(number) {
    var character;
    var result = '';
    for (var i = 0; i < number.length; i += 3) {
      character = parseInt(number.substr(i, 3), 10).toString(16);
      result += '%' + ((character.length % 2 == 0) ? character : '0' + character);
    }
    return decodeURIComponent(result);
  }

  static newPostRequest(ct) {
    return {
      method: 'post',
      headers: {
        'Content-Type': ct,
        'X-Secret': config.SERVER_TOKEN
      }
    };
  }

  static checkAdmin(message) {
    var isAdmin = message.member.roles.cache.find(function(role) {
      return role.name.toLowerCase() === 'pzadmin';
    });
    if (isAdmin == null) {
      message.react('🔒');
      return false;
    }
    return true;
  }

}


class SubsHelper {

  static async daemon(subscribeUrl, dataHandler) {
    var url = null;
    while (running && url == null) {
      while (running && url == null) {
        url = await SubsHelper.subscribe(subscribeUrl, function(pollUrl) {
          Logger.info(subscribeUrl + ' => ' + pollUrl);
        });
        if (running && url == null) {
          await Util.sleep(12000);
        }
      }
      if (running && url != null && url != false) {
        await SubsHelper.poll(url, dataHandler);
      }
      if (url != false) {
        url = null;
      }
    }
  }

  static async subscribe(subscribeUrl, dataHandler) {
    return await fetch(subscribeUrl, Util.newPostRequest('application/json'))
      .then(function(response) {
        if (response.status === 404) return false;
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        if (json === false) return false;
        dataHandler(json.url);
        return json.url;
      })
      .catch(Logger.error);  // return null
  }

  static async poll(url, dataHandler) {
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
          if (Util.isEmptyObject(data)) return true;
          return dataHandler(data);
        })
        .catch(function(error) {
          Logger.error(error);
          return false;
        });
    }
  }

}


class InstancesService {
  #channel = null;
  #current = null;
  #instances = {};

  async startup(channel) {
    this.#channel = channel;
    this.#instances = await fetch(config.SERVER_URL + '/instances')
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        return json;
      })
      .catch(Logger.error);
    this.#current = Util.getFirstKey(this.#instances);
    Logger.info('Instances...');
    Logger.raw(this.#instances);
    for (var instance in this.#instances) {
      if (this.#instances[instance].module === 'projectzomboid') {
         HandlerProjectZomboid.startup(channel, instance, this.#instances[instance].url);
      }
    }
  }

  currentInstance() {
    return this.#current;
  }

  createInstance(data) {
    var instance = data.identity;
    this.#instances[instance] = {
      module: data.module,
      url: config.SERVER_URL + '/instances/' + instance
    };
    this.#current = instance;
    if (this.#instances[instance].module === 'projectzomboid') {
       HandlerProjectZomboid.startup(this.#channel, instance, this.#instances[instance].url);
    }
  }

  useInstance(instance) {
    if (this.#instances.hasOwnProperty(instance)) {
      this.#current = instance;
    }
  }

  deleteInstance(instance) {
    if (this.#instances.hasOwnProperty(instance)) {
      delete this.#instances[instance]
      if (instance === this.#current) {
        this.#current = Util.getFirstKey(this.#instances);
      }
    }
  }

  getInstancesText() {
    var instances = Object.keys(this.#instances);
    if (instances.length === 0) {
      return '```No instances found.```';
    }
    var result = '```';
    for (var i = 0; i < instances.length; i++) {
      if (instances[i] === instancesService.currentInstance()) {
        result += '=> ';
      } else {
        result += '   ';
      }
      result += instances[i] + '\n';
    }
    result += '```';
    return result;
  }

  createHandler(message, instance, command, data) {
    if (instance == null) {
      instance = this.#current;
    }
    if (instance == null) return null;
    if (!this.#instances.hasOwnProperty(instance)) return null;
    if (this.#instances[instance].module === 'projectzomboid'
          && Util.prototypeIncludesProperty(HandlerProjectZomboid.prototype, command)) {
       return new HandlerProjectZomboid(message, this.#instances[instance].url, data);
    }
    return null;
  }

}


class MessageHttpTool {
  #message;
  #baseurl;

  constructor(message, baseurl) {
    this.#message = message;
    this.#baseurl = baseurl;
  }

  get baseurl() {
    return this.#baseurl;
  }

  error(value, message) {
    Logger.error(value);
    message.react('⛔');
  }

  doGet(path, tostring) {
    var self = this;
    var message = this.#message;
    fetch(this.#baseurl + path)
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        message.channel.send(tostring(json));
      })
      .catch(function(error) {
        self.error(error, message);
      });
  }

  doPost(path, body = null, dataHandler = null) {
    var self = this;
    var message = this.#message;
    if (!Util.checkAdmin(message)) return;
    var request = Util.newPostRequest('application/json');
    if (Util.isString(body)) {
      request = Util.newPostRequest('text/plain');
      request.body = body.replace(/\r\n/g, '\n');
    } else if (body != null) {
      request.body = JSON.stringify(body);
    }
    fetch(this.#baseurl + path, request)
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        if (response.status === 204) return null;
        return response.json();
      })
      .then(function(json) {
        if (json != null && json.hasOwnProperty('error')) {
          throw new Error(json.error);
        }
        if (dataHandler == null) {
          message.react('✅');
        } else {
          dataHandler(message, json);
        }
      })
      .catch(function(error) {
        self.error(error, message);
      })
      .finally(function() {
        if (message.content === config.CMD_PREFIX + 'shutdown') {
          shutdown();
        }
      });
    return true;
  }

  static subsToFileDataHandler(message, json) {
    if (json == null || !json.hasOwnProperty('url')) {
      message.react('✅');
      return;
    }
    message.react('⌛');
    var fname = message.id + '.text';
    var fpath = '/tmp/' + fname;
    var fstream = fs.createWriteStream(fpath);
    fstream.on('error', Logger.error);
    SubsHelper.poll(json.url, function(data) {
      fstream.write(data);
      fstream.write('\n');
      return true;
    }).then(function() {
        fstream.end();
        message.reactions.removeAll()
          .then(function() { message.react('✅'); })
          .catch(Logger.error);
        message.channel.send({ files: [{ attachment: fpath, name: fname }] })
          .then(function() { fs.unlink(fpath, Logger.error); });
      });
  }

}


class HandlerSystem {
  #httptool;
  #message;
  #data;

  constructor(message, data) {
    this.#httptool = new MessageHttpTool(message, config.SERVER_URL);
    this.#message = message;
    this.#data = data;
  }

  instances() {
    this.#message.channel.send(instancesService.getInstancesText());
  }

  use() {
    if (!Util.checkAdmin(this.#message)) return;
    if (this.#data.length > 0) {
      instancesService.useInstance(this.#data[0]);
      this.#message.channel.send(instancesService.getInstancesText());
    }
  }

  create() {
    if (this.#data.length < 2) return;
    var body = { identity: this.#data[0], module: this.#data[1] };
    this.#httptool.doPost('/instances', body, function(message, json) {
      instancesService.createInstance(body);
      message.channel.send(instancesService.getInstancesText());
    });
  }

  shutdown() {
    this.#httptool.doPost('/system/shutdown');
  }

  help() {
    if (this.#data.length === 0) {
      var result = '```SYSTEM COMMANDS\n' + config.CMD_PREFIX;
      result += staticData.system.help.join('\n' + config.CMD_PREFIX);
      this.#message.channel.send(result + '```');
    }
  }

}


class HandlerProjectZomboid {
  #instance;
  #httptool;
  #message;
  #data;

  constructor(message, baseurl, data) {
    var parts = baseurl.split('/');
    this.#instance = parts[parts.length - 1];
    this.#httptool = new MessageHttpTool(message, baseurl);
    this.#message = message;
    this.#data = data;
  }

  static startup(channel, instance, url) {
    SubsHelper.daemon(url + '/players/subscribe', function(json) {
      var result = '';
      if (json.event === 'login') { result += 'LOGIN '; }
      if (json.event === 'logout') { result += 'LOGOUT '; }
      result += json.player.name;
      if (json.player.steamid != null) {
        result += ' [' + json.player.steamid + '] ' + instance;
      }
      channel.send(result);
      return true;
    });
  }

  server() {
    var instance = this.#instance;
    var data = this.#data;
    if (data.length === 1) {
      var baseurl = this.#httptool.baseurl;
      this.#httptool.doPost('/server/' + data[0], null, function(message, json) {
        if (data[0] === 'start' || data[0] === 'restart') {
          message.react('⌛');
          SubsHelper.subscribe(baseurl + '/server/subscribe', function(pollUrl) {
            SubsHelper.poll(pollUrl, function(data) {
              if (data != null && data.running && data.state === 'STARTED') {
                message.reactions.removeAll()
                  .then(function() { message.react('✅'); })
                  .catch(Logger.error);
                return false;
              }
              return true;
            });
          });
        } else if (data[0] === 'delete') {
          instancesService.deleteInstance(instance);
          message.react('✅');
        } else {
          message.react('✅');
        }
      });
      return;
    }
    this.#httptool.doGet('/server', function(body) {
      var result = '```Server is ';
      if (!body.running) {
        result += 'DOWN```';
        return result;
      }
      result += body.state + '\n';
      var dtl = body.details;
      if (dtl.hasOwnProperty('version')) { result += 'Version:  ' + dtl.version + '\n'; }
      if (dtl.hasOwnProperty('ingametime')) { result += 'Ingame:   ' + dtl.ingametime + '\n'; }
      return result + '```';
    });
  }

  config() {
    var prefix = this.#httptool.baseurl + '/config/';
    var result = prefix + 'jvm\n';
    result += prefix + 'options\n';
    result += prefix + 'ini\n';
    result += prefix + 'sandbox\n';
    result += prefix + 'spawnpoints\n';
    result += prefix + 'spawnregions\n';
    this.#message.channel.send(result);
  }

  setconfig() {
    var httptool = this.#httptool;
    var message = this.#message;
    var data = [...this.#data];
    if (data.length < 1) return;
    if (message.attachments.length < 1) return;
    fetch(message.attachments.first().url)
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.text();
      })
      .then(function(body) {
        if (body != null) {
          httptool.doPost('/config/' + data.shift(), body);
        }
      })
      .catch(function(error) {
        httptool.error(error, message);
      });
  }

  log() {
    this.#message.channel.send(this.#httptool.baseurl + '/log');
  }

  world() {
    var data = [...this.#data];
    if (data.length < 1) return;
    var cmd = data.shift();
    var body = null;
    if (data.length > 0 && cmd === 'broadcast') {
      body = { message: data.join(' ') };
    }
    this.#httptool.doPost('/world/' + cmd, body);
  }

  deployment() {
    var data = [...this.#data];
    if (data.length < 1) return;
    var cmd = data.shift();
    var body = null;
    if (cmd === 'install-runtime') {
      body = { wipe: true, validate: true };
      if (data.length > 0) { body.beta = data[0]; }
    }
    this.#httptool.doPost('/deployment/' + cmd, body, MessageHttpTool.subsToFileDataHandler);
  }

  players() {
    this.#httptool.doGet('/players', function(body) {
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
  }

  player() {
    var data = [...this.#data];
    if (data.length < 2) return;
    var name = Util.stringToBase10(data.shift());
    var cmd = data.shift();
    var body = null;
    if (data.length > 0) {
      if (cmd === 'set-access-level') {
        body = { level: data[0] };
      } else if (cmd === 'tele-to') {
        body = { toplayer: Util.stringToBase10(data[0]) };
      } else if (cmd === 'tele-at') {
        body = { location: data[0] };
      } else if (cmd === 'spawn-horde') {
        body = { count: data[0] };
      } else if (cmd === 'spawn-vehicle') {
        body = { module: data[0], item: data[1] };
      } else if (cmd === 'give-xp') {
        body = { skill: data[0], xp: data[1] };
      } else if (cmd === 'give-item') {
        body = { module: data[0], item: data[1] };
        if (data.length > 2) { body.count = data[2]; }
      }
    }
    this.#httptool.doPost('/players/' + name + '/' + cmd, body);
  }

  whitelist() {
    var httptool = this.#httptool;
    var message = this.#message;
    var data = [...this.#data];
    if (data.length < 1) return;
    var cmd = data.shift();
    var name = null;
    var body = null;
    if (cmd === 'add-name') {
      body = { player: Util.stringToBase10(data[0]), password: data[1] };
      httptool.doPost('/whitelist/add', body);
    } else if (cmd === 'remove-name') {
      body = { player: Util.stringToBase10(data[0]) };
      httptool.doPost('/whitelist/remove', body);
    } else if (cmd === 'add-id') {
      client.users.fetch(data[0], true, true)
        .then(function(user) {
          var pwd = Math.random().toString(16).substr(2, 8);
          name = user.tag.replace(/ /g, '').replace('#', '');
          Logger.info('Add user: ' + data[0] + ' ' + name);
          body = { player: Util.stringToBase10(name), password: pwd };
          if (httptool.doPost('/whitelist/add', body)) {
            user.send(config.WHITELIST_DM.replace('${user}', name).replace('${pass}', pwd));
          }
        })
        .catch(function(error) {
          httptool.error(error, message);
        });
    } else if (cmd === 'remove-id') {
      client.users.fetch(data[0], true, true)
        .then(function(user) {
          name = user.tag.replace(/ /g, '').replace('#', '');
          Logger.info('Remove user: ' + data[0] + ' ' + name);
          body = { player: Util.stringToBase10(name) };
          httptool.doPost('/whitelist/remove', body);
        })
        .catch(function(error) {
          httptool.error(error, message);
        });
    }
  }

  banlist() {
    var data = [...this.#data];
    if (data.length < 2) return;
    var cmd = data.shift() + '-id';
    var body = { steamid: data.shift() };
    this.#httptool.doPost('/banlist/' + cmd, body);
  }

  help() {
    var channel = this.#message.channel;
    if (this.#data.length === 0) {
      var s = '```PROJECT ZOMBOID COMMANDS\n' + config.CMD_PREFIX;
      channel.send(s + staticData.projectzomboid.help1.join('\n' + config.CMD_PREFIX) + '```');
      channel.send(s + staticData.projectzomboid.help2.join('\n' + config.CMD_PREFIX) + '```');
      channel.send(s + staticData.projectzomboid.help3.join('\n' + config.CMD_PREFIX) + '```');
      return;
    }
    var query = this.#data.join('').replaceAll('-', '');
    if (staticData.projectzomboid.hasOwnProperty(query)) {
      channel.send(staticData.projectzomboid[query].join('\n'));
    } else {
      channel.send('No more help available.');
    }
  }

}


function startup() {
  running = true;
  Logger.info('Logged in as ' + client.user.tag);
  client.channels.fetch(config.EVENTS_CHANNEL_ID)
    .then(function(channel) {
      Logger.info('Publishing events to ' + channel.id);
      instancesService.startup(channel);
      if (config.hasOwnProperty('STARTUP_REPORT')) {
        fs.promises.access(config.STARTUP_REPORT, fs.constants.F_OK)
          .then(function() {
            Logger.info('Sending startup report.');
            channel.send({
              content: '**Startup Report**',
              files: [{ attachment: config.STARTUP_REPORT, name: 'report.text' }] });
          })
          .catch(function() {
            Logger.info('No startup report found.');
          });
      }
    })
    .catch(Logger.error);
}

function handleMessage(message) {
  //if (message.author.bot) return;
  if (!message.content.startsWith(config.CMD_PREFIX)) return;
  var data = Util.commandLineToList(message.content.slice(1));
  var command = data.shift().toLowerCase();
  var instance = null;
  var parts = command.split('.');
  if (parts.length === 1) {
    command = parts[0];
  } else {
    instance = parts[0];
    command = parts[1];
  }
  var handlers = [];
  if (Util.prototypeIncludesProperty(HandlerSystem.prototype, command)) {
    handlers.push(new HandlerSystem(message, data));
  }
  var handler = instancesService.createHandler(message, instance, command, data);
  if (handler != null) {
    handlers.push(handler);
  }
  if (handlers.length === 0) {
    message.react('⛔');
    return;
  }
  Logger.info(message.member.user.tag + ' ' + message.content);
  for (var i = 0; i < handlers.length; i++) {
    handlers[i][command]();
  }
}

function shutdown() {
  running = false;
  Logger.info('*** END ServerLink Bot ***');
  client.destroy();
}


// MAIN

var running = false;
Logger.info('*** START ServerLink Bot ***');
const config = { ...require(process.argv[2]), ...require(process.argv[3]) };
Logger.info('Initialised with config...');
Logger.raw(config);

const staticData = require('./constants.json');
const fs = require('fs');
const fetch = require('node-fetch');
const instancesService = new InstancesService();
const { Client, Intents } = require('discord.js');
const client = new Client({ intents: ['GUILDS', 'GUILD_MESSAGES', 'DIRECT_MESSAGES'], partials: ['CHANNEL'] });

client.once('ready', startup);
client.on('messageCreate', handleMessage);
process.on('SIGTERM', shutdown);
client.login(config.BOT_TOKEN);
