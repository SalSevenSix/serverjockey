
export const devDom = 'Workshop ID: 9999999999< ' +
                      'Mod ID: Alpha< Mod ID: Beta Xyz< Mod ID: Gamma< ' +
                      'Map Folder: Green< Map Folder: Blue Abc';

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

export function processResults(dom, ini, updated) {
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
  self.workshop = {
    available: !self.ini.workshops.includes(self.dom.workshop),
    selected: [...self.ini.workshops],
    add: function() {
      self.workshop.selected = [...self.workshop.selected, self.dom.workshop];
      self.workshop.available = false;
      updated();
    },
    remove: function() {
      self.mods.selected = self.mods.selected.filter(function(value) { return !self.dom.mods.includes(value); });
      self.mods.available = [...self.dom.mods];
      self.maps.selected = self.maps.selected.filter(function(value) { return !self.dom.maps.includes(value); });
      self.maps.available = [...self.dom.maps];
      self.workshop.selected = self.workshop.selected.filter(function(value) { return value != self.dom.workshop; });
      self.workshop.available = true;
      updated();
    }
  };
  self.mods = {
    available: self.dom.mods.filter(function(value) { return !self.ini.mods.includes(value); }),
    selected: [...self.ini.mods],
    addTop: function(item) {
      self.mods.selected = [item, ...self.mods.selected];
      self.mods.available = self.mods.available.filter(function(value) { return item != value; });
      updated();
    },
    addBottom: function(item) {
      self.mods.selected = [...self.mods.selected, item];
      self.mods.available = self.mods.available.filter(function(value) { return item != value; });
      updated();
    },
    remove: function(item) {
      self.mods.available = [...self.mods.available, item];
      self.mods.selected = self.mods.selected.filter(function(value) { return item != value; });
      updated();
    },
    bumpUp: function(item) {
      let index = self.mods.selected.indexOf(item);
      if (index === 0) return;
      self.mods.selected.splice(index, 1);
      self.mods.selected.splice(index - 1, 0, item);
      updated();
    },
    bumpDown: function(item) {
      let index = self.mods.selected.indexOf(item);
      if (index === self.mods.selected.length - 1) return;
      self.mods.selected.splice(index, 1);
      self.mods.selected.splice(index + 1, 0, item);
      updated();
    }
  };
  self.maps = {
    available: self.dom.maps.filter(function(value) { return !self.ini.maps.includes(value); }),
    selected: [...self.ini.maps],
    addTop: function(item) {
      self.maps.selected = [item, ...self.maps.selected];
      self.maps.available = self.maps.available.filter(function(value) { return item != value; });
      updated();
    },
    addBottom: function(item) {
      self.maps.selected = [...self.maps.selected, item];
      self.maps.available = self.maps.available.filter(function(value) { return item != value; });
      updated();
    },
    remove: function(item) {
      self.maps.available = [...self.maps.available, item];
      self.maps.selected = self.maps.selected.filter(function(value) { return item != value; });
      updated();
    },
    bumpUp: function(item) {
      let index = self.maps.selected.indexOf(item);
      if (index === 0) return;
      self.maps.selected.splice(index, 1);
      self.maps.selected.splice(index - 1, 0, item);
      updated();
    },
    bumpDown: function(item) {
      let index = self.maps.selected.indexOf(item);
      if (index === self.maps.selected.length - 1) return;
      self.maps.selected.splice(index, 1);
      self.maps.selected.splice(index + 1, 0, item);
      updated();
    }
  };
  self.generateIni = function() {
    let result = [];
    self.raw.ini.split('\n').forEach(function(line) {
      if (line.startsWith('WorkshopItems=')) {
        result.push('WorkshopItems=' + self.workshop.selected.join(';'));
      } else if (line.startsWith('Mods=')) {
        result.push('Mods=' + self.mods.selected.join(';'));
      } else if (line.startsWith('Map=')) {
        result.push('Map=' + self.maps.selected.join(';'));
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
