import * as msgutil from '../util/msgutil.js';
import * as logger from '../util/logger.js';

function chatbotHandler({ context, message }, gamename) {
  msgutil.reactWait(message);
  const input = msgutil.extractCommandLine(message);
  context.llmClient.chatbot({ input, gamename }).then(function(text) {
    msgutil.sendText(message, text, false);
    msgutil.rmReacts(message, msgutil.reactSuccess, logger.error);
  });
}

export function chatbot(gamename) {
  return function(args) { chatbotHandler(args, gamename); };
}
