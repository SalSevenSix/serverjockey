import * as msgutil from '../util/msgutil.js';
import * as logger from '../util/logger.js';

export function chatbot({ context, instance, message }) {
  msgutil.reactWait(message);
  const input = msgutil.extractCommandLine(message);
  const gamename = context.instancesService.getModuleName(instance);
  context.llmClient.chatbot({ input, gamename }).then(function(text) {
    msgutil.sendText(message, text, false);
    msgutil.rmReacts(message, msgutil.reactSuccess, logger.error);
  });
}
