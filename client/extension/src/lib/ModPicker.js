import { baseurl, logError, newGetRequest, noStorage } from '$lib/sjgmsapi';

const workshopCacheKey = 'sjgmsExtensionWorkshopCache';

export const devDom = '<div class="workshopItemTitle">Dummy Mod</div> ' +
                      'Workshop ID: 9999999999< ' +
                      'Mod ID: Alpha< Mod ID: Beta Xyz< Mod ID: Gamma< ' +
                      'Map Folder: Green< Map Folder: Blue Abc';

function toUnique(arr, reverse=false) {
  let result = [...arr];
  if (reverse) { result.reverse(); }
  result = result.filter(function(value, index, array) { return array.indexOf(value) === index; });
  if (reverse) { result.reverse(); }
  return result
}

function domExtract(dom, cutlen, regex, single=false) {
  let result = dom.match(regex);
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

function jsonExtract(data) {
  const [mods, maps] = [[], []];
  const lines = data.description.split('\n');
  lines.reverse();
  let checking = true;
  lines.forEach(function(line) {
    if (checking && line) {
      if (line.startsWith('Map Folder:')) {
        maps.push(line.substring(12));
      } else if (line.startsWith('Mod ID:')) {
        mods.push(line.substring(8));
      } else if (line.startsWith('Workshop ID:')) {
        checking = false;
      }
    }
  });
  maps.reverse();
  mods.reverse();
  return { workshop: data.publishedfileid, name: data.title, mods: mods, maps: maps };
}

function bumpItemUp(items, item) {
  const index = items.indexOf(item);
  if (index === 0) {
    items = items.filter(function(value) { return item != value; });
    items = [...items, item];
  } else {
    items.splice(index, 1);
    items.splice(index - 1, 0, item);
  }
  return items;
}

function bumpItemDown(items, item) {
  const index = items.indexOf(item);
  if (index === items.length - 1) {
    items = items.filter(function(value) { return item != value; });
    items = [item, ...items];
  } else {
    items.splice(index, 1);
    items.splice(index + 1, 0, item);
  }
  return items;
}


const workshopCache = {
  data: null,
  cache: function() {
    if (workshopCache.data) return workshopCache.data;
    workshopCache.data = {};
    if (noStorage) return workshopCache.data;
    let stored = localStorage.getItem(workshopCacheKey);
    if (!stored) return workshopCache.data;
    stored = JSON.parse(stored);
    const now = Date.now();
    Object.keys(stored).forEach(function(workshop) {
      if (now - stored[workshop].updated < 172800000) {  // 48 hours
        workshopCache.data[workshop] = stored[workshop];
      }
    });
    return workshopCache.data;
  },
  save: function() {
    if (noStorage) return;
    localStorage.setItem(workshopCacheKey, JSON.stringify(workshopCache.data));
  },
  add: function(workshop, name, mods, maps) {
    const item = { updated: Date.now(), name: name, mods: mods };
    if (maps.length > 0) { item.maps = maps; }
    workshopCache.cache()[workshop] = item;
  },
  get: function(workshop) {
    const item = workshopCache.cache()[workshop];
    if (!item) return null;
    if (!item.maps) { item.maps = []; }
    return item;
  },
  name: function(workshop) {
    const item = workshopCache.get(workshop);
    return item ? item.name : '';
  },
  uncached: function(workshops, limit=10) {
    const result = [];
    if (workshops.length === 0 || limit < 1) return result;
    for (let i = 0; i < workshops.length; i++) {
      const item = workshopCache.get(workshops[i]);
      if (!item) { result.push(workshops[i]); }
      if (result.length >= limit) return result;
    }
    return result;
  }
};

async function fetchWorkshops(workshops) {
  const uncached = workshopCache.uncached(workshops);
  if (uncached.length === 0) return false;
  return await fetch(baseurl('/steamapi/published-file-details?ids=' + uncached.join(',')), newGetRequest())
    .then(function(response) {
      if (!response.ok) { throw new Error('Status: ' + response.status); }
      return response.json();
    })
    .then(function(json) {
      if (!json.response || !json.response.publishedfiledetails) return false;
      json.response.publishedfiledetails.forEach(function(data) {
        const extracted = jsonExtract(data);
        workshopCache.add(extracted.workshop, extracted.name, extracted.mods, extracted.maps);
      });
      workshopCache.save();
      return true;
    })
    .catch(function(error) {
      logError(error);
      return false;
    });
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


export function processResults(dom, ini, updated) {
  const self = { raw: { dom: dom, ini: ini } };
  let cleanDom = dom.replaceAll('<span class="searchedForText">', '').replaceAll('</span>', '');
  self.dom = {
    workshop: domExtract(cleanDom, 13, /Workshop ID:(.*?)</g, true),
    name: domExtract(cleanDom, 26, /class="workshopItemTitle">(.*?)</g, true),
    mods: domExtract(cleanDom, 8, /Mod ID:(.*?)</g),
    maps: domExtract(cleanDom, 12, /Map Folder:(.*?)</g)
  };
  cleanDom = null;  // free memory
  workshopCache.add(self.dom.workshop, self.dom.name, self.dom.mods, self.dom.maps);
  workshopCache.save();
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
    remove: function(workshop=null) {
      if (!workshop) { workshop = self.dom.workshop; }
      let mods = self.dom.mods;
      let maps = self.dom.maps;
      if (workshop == self.dom.workshop) {
        self.mods.available = [...mods];
        self.maps.available = [...maps];
        self.workshop.available = true;
      } else {
        const cached = workshopCache.get(workshop);
        if (!cached) return;
        mods = cached.mods;
        maps = cached.maps;
      }
      self.mods.selected = self.mods.selected.filter(function(value) { return !mods.includes(value); });
      self.maps.selected = self.maps.selected.filter(function(value) { return !maps.includes(value); });
      self.workshop.selected = self.workshop.selected.filter(function(value) { return value != workshop; });
      updated();
    },
    api: {
      filebaseurl: 'https://steamcommunity.com/sharedfiles/filedetails/?id=',
      name: workshopCache.name,
      fetch: async function() {
        let result = await fetchWorkshops(self.workshop.selected);
        updated(false);
        return result;
      }
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
      self.mods.selected = bumpItemUp(self.mods.selected, item);
      updated();
    },
    bumpDown: function(item) {
      self.mods.selected = bumpItemDown(self.mods.selected, item);
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
      self.maps.selected = bumpItemUp(self.maps.selected, item);
      updated();
    },
    bumpDown: function(item) {
      self.maps.selected = bumpItemDown(self.maps.selected, item);
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
