import { newPostRequest, newGetRequest } from '$lib/util/sjgmsapi';
import { notifyInfo, notifyError } from '$lib/util/notifications';
import { textAreaModal } from '$lib/modal/modals';

function saveFile(url, name, text) {
  const request = newPostRequest('text/plain');
  request.body = text;
  fetch(url, request)
    .then(function(response) {
      if (!response.ok) throw new Error('Status: ' + response.status);
      notifyInfo(name + ' saved.');
    })
    .catch(function() {
      notifyError('Failed to update ' + name);
    });
}

export function loadAndEditFile(url, name) {
  fetch(url, newGetRequest())
    .then(function(response) {
      if (!response.ok) throw new Error('Status: ' + response.status);
      return response.text();
    })
    .then(function(text) {
      textAreaModal(name, text, function(updated) { saveFile(url, name, updated); });
    })
    .catch(function() {
      notifyError('Failed to load ' + name);
    });
}

export const worldActions = [
  { 'key': 'wipe-world-save', 'name': 'Reset Save',
    'desc': 'Reset the default world save only.' },
  { 'key': 'wipe-world-logs', 'name': 'Delete Logs',
    'desc': 'Delete the log files only.' },
  { 'key': 'wipe-world-autobackups', 'name': 'Delete Autobackups',
    'desc': 'Delete the automatic server created backups.' },
  { 'key': 'wipe-world-all', 'name': 'Reset All', 'icon': 'fa-explosion',
    'desc': 'Reset all of the above.' }];
