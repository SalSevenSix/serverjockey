import * as cutil from 'common/util/util';

function processSection(context, httptool, message, data, section) {
  const cmd = context.config.CMD_PREFIX;
  if (data.length === 0) {
    let [index, header] = [1, '```\n'];
    if (section.title) { header += section.title + '\n'; }
    header += cmd;
    while (cutil.hasProp(section, 'help' + index)) {
      message.channel.send(header + section['help' + index].join('\n' + cmd) + '\n```');
      if (index === 1) { header = '```\n' + cmd; }
      index += 1;
    }
    return null;
  }
  const query = data.join('-');
  if (query === 'title' || !cutil.hasProp(section, query)) return false;
  if (cutil.isString(section[query])) {
    httptool.doGet(section[query], function(body) { return [body]; });
  } else {
    message.channel.send(section[query].map(function(line) {
      return line && line.slice(0, 2) === '`!' ? '`' + cmd + line.slice(2) : line;
    }).join('\n'));
  }
  return true;
}

function processData(context, httptool, message, data, helpData) {
  const sections = Array.isArray(helpData) ? helpData : [helpData];
  let [index, done] = [0, false];
  while (index < sections.length && !done) {
    done = processSection(context, httptool, message, data, sections[index]);
    index += 1;
  }
  if (done === false) { message.channel.send('No more help available.'); }
}

export function process(helpData) {
  return function({ context, httptool, message, data }) {
    processData(context, httptool, message, data, helpData);
  };
}

export function newHelpBuilder() {
  const [self, data] = [{}, {}];
  let paragraph = 0;

  const current = function() { return 'help' + paragraph; };

  self.title = function(value) {
    data.title = value;
    return self;
  };

  self.next = function() {
    paragraph += 1;
    data[current()] = [];
    return self;
  };

  self.add = function(value) {
    if (Array.isArray(value)) { data[current()].push(...value); }
    else { data[current()].push(value); }
    return self;
  };

  self.addHelp = function(command, value) {
    let indexes = [command.indexOf('"'), command.indexOf('{'), command.indexOf(':')];
    indexes = indexes.filter(function(index) { return index > -1; });
    if (indexes.length === 0) { indexes.push(-1); }
    const index = indexes.reduce(function(a, b) { return a > b ? b : a; });
    let key = command;
    if (index > -1) { key = key.slice(0, index); }
    key = key.trim().replaceAll(' ', '-');
    data[key] = value;
    return self;
  };

  self.buildData = function() { return { ...data }; };
  return self.next();
}
