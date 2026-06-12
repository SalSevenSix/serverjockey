import { newPostRequest, newGetRequest, checkReponseOk, getReponseText } from '$lib/util/sjgmsapi';
import { notifyInfo, notifyError } from '$lib/util/notifications';
import { textAreaModal } from '$lib/modal/modals';

function saveFile(url, name, text) {
  const request = newPostRequest('text/plain');
  request.body = text;
  fetch(url, request)
    .then(function(response) {
      checkReponseOk(response);
      notifyInfo(name + ' saved.');
    })
    .catch(function() { notifyError('Failed to update ' + name); });
}

export function loadAndEditFile(url, name) {
  fetch(url, newGetRequest())
    .then(function(response) { return getReponseText(response); })
    .then(function(text) {
      textAreaModal(name, text, function(updated) { saveFile(url, name, updated); });
    })
    .catch(function() { notifyError('Failed to load ' + name); });
}
