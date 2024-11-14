export const devDom = '<div class="workshopItemTitle">Dummy Mod</div> ' +
                      'Workshop ID: 9999999999< ' +
                      'Mod ID: Alpha< Mod ID: Beta Xyz< Mod ID: Gamma< ' +
                      'Map Folder: Green< Map Folder: Blue Abc';

function unique(value, index, array) {
  return array.indexOf(value) === index;
}

function domExtractItem(dom, cutlen, regex, single=false) {
  let result = dom.match(regex);
  if (!result) return single ? null : [];
  result = result.map(function(value) {
    value = value.substring(cutlen, value.length - 1);
    value = value.replaceAll('&amp;', '&').replaceAll('&lt;', '<').replaceAll('&gt;', '>');
    return value;
  });
  return single ? result[result.length - 1] : result.filter(unique);
}

function iniExtractItem(ini, cutlen, regex) {
  let result = ini.match(regex);
  if (!result) return [];
  result = result[result.length - 1].substring(cutlen);
  result = result.split(';');
  result = result.filter(function(value) { return value.trim(); });
  return result.filter(unique);
}


export function domClean(dom) {
  return dom.replaceAll('<span class="searchedForText">', '').replaceAll('</span>', '');
}

export function isModPage(dom) {
  if (!dom) return false;
  const expected = [
    'steamcommunity.com/app/108600">Project Zomboid',
    'steamcommunity.com/app/108600/workshop/">Workshop',
    'Workshop ID:', 'Mod ID:'];
  const actual = expected.filter(function(value) { return dom.includes(value); });
  if (expected.length != actual.length) return false;
  return !dom.includes('<div id="mainContentsCollection">');
}

export function domExtract(dom) {
  const workshopItemTitle = domExtractItem(dom, 26, /class="workshopItemTitle">(.*?)</g, true);
  let index = dom.indexOf('class="workshopItemDescription"');
  if (index > -1) { dom = dom.substring(index); }
  index = dom.indexOf('class="workshopItemDescriptionTitle"');
  if (index > -1) { dom = dom.substring(0, index); }
  index = dom.indexOf('class="commentthread_area"');
  if (index > -1) { dom = dom.substring(0, index); }
  dom = dom.replaceAll('<b>', '').replaceAll('</b>', '');
  dom = dom.replaceAll('<i>', '').replaceAll('</i>', '');
  return {
    workshop: domExtractItem(dom, 13, /Workshop ID:(.*?)</g, true),
    name: workshopItemTitle,
    mods: domExtractItem(dom, 8, /Mod ID:(.*?)</g),
    maps: domExtractItem(dom, 12, /Map Folder:(.*?)</g)
  };
}

export function iniExtract(ini) {
  return {
    workshops: iniExtractItem(ini, 14, /^WorkshopItems=.*$/gm),
    mods: iniExtractItem(ini, 5, /^Mods=.*$/gm),
    maps: iniExtractItem(ini, 4, /^Map=.*$/gm)
  };
}

export function jsonExtract(data) {
  const [mods, maps] = [[], []];
  const lines = data.description.replaceAll('\r', '\n').split('\n');
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
