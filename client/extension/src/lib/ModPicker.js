
// <br><br>Workshop ID: 1896907770<br>Mod ID: FRUsedCarsBETA<br>Mod ID: FRUsedCarsFT<br>Mod ID: FRUsedCarsNLF<br>Mod ID: FRUsedCarsNRN</div>
// ^WorkshopItems=2820127528;2740018049

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

export function processResults(dom, ini) {
  const result = { raw: { dom: dom, ini: ini } };
  result.dom = {
    workshop: domExtract(dom, 13, /Workshop ID:(.*?)</g, true),
    mods: domExtract(dom, 8, /Mod ID:(.*?)</g),
    maps: domExtract(dom, 12, /Map Folder:(.*?)</g)
  };
  result.ini = {
    workshops: iniExtract(ini, 14, /^WorkshopItems=.*$/gm),
    mods: iniExtract(ini, 5, /^Mods=.*$/gm),
    maps: iniExtract(ini, 4, /^Map=.*$/gm)
  };
  result.selected = {
    workshops: [...result.ini.workshops],
    mods: [...result.ini.mods],
    maps: [...result.ini.maps]
  };
  result.selectable = {
    workshop: !result.ini.workshops.includes(result.dom.workshop),
    mods: result.dom.mods.filter(function(value) { return !result.ini.mods.includes(value); }),
    maps: result.dom.maps.filter(function(value) { return !result.ini.maps.includes(value); })
  };
  return result;
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
