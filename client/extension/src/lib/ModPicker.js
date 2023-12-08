
function cleanDom(dom) {
  let result = dom.replaceAll('<span class="searchedForText">', '');
  result = result.replaceAll('</span>', '');
  return result
}

function toUnique(arr, reverse=false) {
  let result = [...arr];
  if (reverse) { result.reverse(); }
  result = result.filter(function(value, index, array) { return array.indexOf(value) === index; });
  if (reverse) { result.reverse(); }
  return result
}

function domExtract(dom, cutlen, regex, single=false) {
  let result = cleanDom(dom).match(regex);
  if (!result) return single ? null : [];
  result = result.map(function(value) { return value.substring(cutlen, value.length - 1); });
  return single ? result[result.length - 1] : toUnique(result, true);
}

function iniExtract(ini, cutlen, regex) {
  let result = ini.match(regex);
  if (!result) return [];
  result = result[result.length - 1].substring(cutlen);
  result = result.split(';');
  result = result.filter(function(value) { return value.trim(); });
  return toUnique(result);
}

export function processResults(dom, ini) {
  const self = { raw: { dom: dom, ini: ini } };
  self.dom = {
    workshop: domExtract(dom, 13, /Workshop ID:(.*?)</g, true),
    mods: domExtract(dom, 8, /Mod ID:(.*?)</g),
    maps: domExtract(dom, 12, /Map Folder:(.*?)</g)
  };
  self.ini = {
    workshops: iniExtract(ini, 14, /^WorkshopItems=.*$/gm),
    mods: iniExtract(ini, 5, /^Mods=.*$/gm),
    maps: iniExtract(ini, 4, /^Map=.*$/gm)
  };
  self.selected = {
    workshops: [...self.ini.workshops],
    mods: [...self.ini.mods],
    maps: [...self.ini.maps]
  };
  self.available = {
    workshop: !self.ini.workshops.includes(self.dom.workshop),
    mods: self.dom.mods.filter(function(value) { return !self.ini.mods.includes(value); }),
    maps: self.dom.maps.filter(function(value) { return !self.ini.maps.includes(value); })
  };
  self.addWorkshop = function() {
    self.selected.workshops = [...self.selected.workshops, self.dom.workshop];
    self.available.workshop = false;
  };
  self.removeWorkshop = function() {
    self.selected.workshops = self.selected.workshops.filter(function(value) {
      return value != self.dom.workshop;
    });
    self.selected.mods = self.selected.mods.filter(function(value) {
      return !self.dom.mods.includes(value);
    });
    self.available.mods = [...self.dom.mods];
    self.selected.maps = self.selected.maps.filter(function(value) {
      return !self.dom.maps.includes(value);
    });
    self.available.maps = [...self.dom.maps];
    self.available.workshop = true;
  };
  self.addModTop = function(mod) {
    self.selected.mods = [mod, ...self.selected.mods];
    self.available.mods = self.available.mods.filter(function(value) { return mod != value; });
  };
  self.addModBottom = function(mod) {
    self.selected.mods = [...self.selected.mods, mod];
    self.available.mods = self.available.mods.filter(function(value) { return mod != value; });
  };
  self.removeMod = function(mod) {
    self.available.mods = [...self.available.mods, mod];
    self.selected.mods = self.selected.mods.filter(function(value) { return mod != value; });
  };
  self.bumpModUp = function(mod) {
    let index = self.selected.mods.indexOf(mod);
    if (index === 0) return;
    self.selected.mods.splice(index, 1);
    self.selected.mods.splice(index - 1, 0, mod);
    self.selected.mods = [...self.selected.mods];
  };
  self.bumpModDown = function(mod) {
    let index = self.selected.mods.indexOf(mod);
    if (index === self.selected.mods.length - 1) return;
    self.selected.mods.splice(index, 1);
    self.selected.mods.splice(index + 1, 0, mod);
    self.selected.mods = [...self.selected.mods];
  };
  self.addMapTop = function(map) {
    self.selected.maps = [map, ...self.selected.maps];
    self.available.maps = self.available.maps.filter(function(value) { return map != value; });
  };
  self.addMapBottom = function(map) {
    self.selected.maps = [...self.selected.maps, map];
    self.available.maps = self.available.maps.filter(function(value) { return map != value; });
  };
  self.removeMap = function(map) {
    self.available.maps = [...self.available.maps, map];
    self.selected.maps = self.selected.maps.filter(function(value) { return map != value; });
  };
  self.bumpMapUp = function(map) {
    let index = self.selected.maps.indexOf(map);
    if (index === 0) return;
    self.selected.maps.splice(index, 1);
    self.selected.maps.splice(index - 1, 0, map);
    self.selected.maps = [...self.selected.maps];
  };
  self.bumpMapDown = function(map) {
    let index = self.selected.maps.indexOf(map);
    if (index === self.selected.maps.length - 1) return;
    self.selected.maps.splice(index, 1);
    self.selected.maps.splice(index + 1, 0, map);
    self.selected.maps = [...self.selected.maps];
  };
  self.generateIni = function() {
    let result = [];
    self.raw.ini.split('\n').forEach(function(line) {
      if (line.startsWith('WorkshopItems=')) {
        result.push('WorkshopItems=' + self.selected.workshops.join(';'));
      } else if (line.startsWith('Mods=')) {
        result.push('Mods=' + self.selected.mods.join(';'));
      } else if (line.startsWith('Map=')) {
        result.push('Map=' + self.selected.maps.join(';'));
      } else {
        result.push(line);
      }
    });
    return result.join('\n');
  };
  return self;
}

export function isModPage(dom) {
  if (!dom) return false;
  const expected = [
    'steamcommunity.com/app/108600">Project Zomboid',
    'steamcommunity.com/app/108600/workshop/">Workshop',
    'Workshop ID:', 'Mod ID:'];
  const actual = expected.filter(function(value) { return dom.includes(value); });
  return expected.length === actual.length;
}
