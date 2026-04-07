import fs from 'fs';
import { fNoop } from 'common/util/util';
import * as logger from './logger.js';

export function fileDelete(path) {
  if (!path) return;
  fs.exists(path, function(exists) {
    if (exists) { fs.unlink(path, logger.error); }
  });
}

export function fileWrite(path, body) {
  if (!path || !body) return;
  fs.writeFile(path, body, logger.error);
}

export function fileSaveArray(path, value) {
  if (!path) return;
  if (!value || value.length === 0) { fileDelete(path); }
  else { fileWrite(path, JSON.stringify(value)); }
}

export function fileRead(path, onLoaded = fNoop, onNotExists = fNoop, onError = fNoop) {
  if (!path) return;
  fs.exists(path, function(exists) {
    if (!exists) return onNotExists();
    fs.readFile(path, function(error, body) {
      if (error) {
        logger.error(error);
        onError();
      } else {
        onLoaded(body);
      }
    });
  });
}
