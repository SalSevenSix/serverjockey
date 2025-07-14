import * as msgutil from '../util/msgutil.js';
import * as logger from '../util/logger.js';

export function chat({ context, instance, message }) {
  if (!msgutil.checkHasRole(message, context.config.PLAYER_ROLE)) return;
  msgutil.reactWait(message);
  const input = msgutil.extractCommandLine(message);
  const gamename = context.instancesService.getModuleName(instance);
  context.llmClient.chatbot({ input, gamename }).then(function(text) {
    msgutil.sendText(message, text, false);
    msgutil.rmReacts(message, msgutil.reactSuccess, logger.error);
  });
}
