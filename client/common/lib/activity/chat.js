import { shortISODateTimeString, urlSafeB64encode } from 'common/util/util';

export const eventsMap = {
  LOGIN: 'fa fa-right-to-bracket',
  DEATH: 'fa fa-skull',
  LOGOUT: 'fa fa-right-to-bracket rotate-180'
};

export function mergeResults(data) {
  const result = [];
  if (data.chat) {
    data.chat.records.forEach(function(record) {
      result.push({ at: record[0], player: record[1], text: record[2] });
    });
  }
  if (data.session) {
    data.session.records.forEach(function(record) {
      result.push({ at: record[0], player: record[2], steamid: record[4], event: record[3] });
    });
  }
  result.sort(function(left, right) {
    return left.at - right.at;
  });
  return result;
}

export function extractResults(data) {
  const last = { at: '', player: '' };
  const result = [];
  let clazz = null;
  data.forEach(function(item) {
    const atString = shortISODateTimeString(item.at);
    const atSection = atString.substring(0, 13);
    if (last.at != atSection) {
      result.push({ clazz: 'row-hdr', ats: atString, at: atSection + 'h' });
      last.at = atSection;
      clazz = null;
    }
    if (!clazz || last.player != item.player) {
      clazz = clazz === 'row-nrm' ? 'row-alt' : 'row-nrm';
    }
    last.player = item.player;
    const entry = { clazz: clazz, ats: atString, at: atString.substring(14), player: item.player };
    if (item.event) {
      entry.event = item.event;
      entry.text = item.steamid;
    } else {
      entry.text = item.text;
    }
    result.push(entry);
  });
  return result;
}

export function extractMeta(data) {
  return { created: data.created, atfrom: data.criteria.atfrom, atto: data.criteria.atto,
    atrange: data.criteria.atto - data.criteria.atfrom };
}

export function querySessions(instance, atrange, player) {
  let url = '/store/player/event';
  url += '?atfrom=' + atrange.atfrom + '&atto=' + atrange.atto;
  url += '&instance=' + instance;
  if (player) { url += '&player=' + urlSafeB64encode(player); }
  url += '&events=' + Object.keys(eventsMap).join(',');
  url += '&verbose';
  return { url: url, error: 'Failed to query player events.' };
}

export function queryChats(instance, atrange, player) {
  let url = '/store/player/chat';
  url += '?atfrom=' + atrange.atfrom + '&atto=' + atrange.atto;
  url += '&instance=' + instance;
  if (player) { url += '&player=' + urlSafeB64encode(player); }
  return { url: url, error: 'Failed to query chat logs.' };
}
