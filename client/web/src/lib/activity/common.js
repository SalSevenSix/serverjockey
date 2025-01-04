import { surl, newGetRequest } from '$lib/util/sjgmsapi';
import { notifyError } from '$lib/util/notifications';


export async function queryFetch(url, errorMessage) {
  return await fetch(surl(url), newGetRequest())
    .then(function(response) {
      if (!response.ok) throw new Error('Status: ' + response.status);
      return response.json();
    })
    .then(function(json) { return json; })
    .catch(function() { notifyError(errorMessage); });
}
