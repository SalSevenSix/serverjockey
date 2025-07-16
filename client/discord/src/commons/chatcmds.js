import * as cutil from 'common/util/util';
import * as msgutil from '../util/msgutil.js';
import * as logger from '../util/logger.js';

export function chat({ context, chatbot, message }) {
  if (!msgutil.checkHasRole(message, context.config.PLAYER_ROLE)) return;
  const input = msgutil.extractCommandLine(message);
  if (input) {
    msgutil.reactWait(message);
    chatbot.request(input).then(function(text) {
      msgutil.sendText(message, '@: ' + text, false);
      cutil.sleep(1000).then(function() { msgutil.rmReacts(message, msgutil.reactSuccess, logger.error); });
    });
  } else {
    chatbot.reset();
    msgutil.reactSuccess(message);
  }
}
