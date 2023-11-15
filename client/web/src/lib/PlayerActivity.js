import { newGetRequest } from '$lib/sjgmsapi';
import { notifyError } from '$lib/notifications';

export function extractActivity(eData, lData) {
  let result = { created: eData.created, atfrom: eData.criteria.atfrom, atto: eData.criteria.atto,
                 atrange: eData.criteria.atto - eData.criteria.atfrom, players: [] };
  return result;
}

async function queryFetch(url, errorMessage) {
  return await fetch(url, newGetRequest())
    .then(function(response) {
      if (!response.ok) throw new Error('Status: ' + response.status);
      return response.json();
    })
    .then(function(json) { return json; })
    .catch(function(error) { notifyError(errorMessage); });
}

export async function queryEvents(criteria) {
  let url = '/store/player/event?atfrom=' + criteria.atfrom + '&atto=' + criteria.atto;
  if (criteria.instance) { url += '&instance=' + criteria.instance; }
  return await queryFetch(url, 'Failed to query player events.');
}

export async function queryLastEvent(criteria) {
  let url = '/store/player/event?atgroup=max&atto=' + criteria.atfrom;
  if (criteria.instance) { url += '&instance=' + criteria.instance; }
  return await queryFetch(url, 'Failed to query last player event.');
}
