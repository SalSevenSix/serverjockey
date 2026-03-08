import fetch from 'node-fetch';
import * as util from '../util/util.js';
import * as logger from '../util/logger.js';

export function newChatbotHandler(context, instance, url) {
  const data = { chatbot: null };

  fetch(url + '/console/say', util.newPostRequest('application/json', context.config.SERVER_TOKEN))
    .then(function(response) {
      if ([200, 204, 400, 409].includes(response.status)) {  // This confirms the Say service is available
        data.chatbot = context.llmClient.newChatbot(context.instancesService.getModuleName(instance));
      }
    })
    .catch(logger.error);

  return function(input) {
    if (!data.chatbot || !input || !input.startsWith(context.config.CMD_PREFIX)) return;
    if (input.trim() === context.config.CMD_PREFIX) return data.chatbot.reset();
    data.chatbot.request(input.slice(context.config.CMD_PREFIX.length).trim())
      .then(function(text) {
        const request = util.newPostRequest('application/json', context.config.SERVER_TOKEN);
        request.body = JSON.stringify({ player: '@', text: text });
        fetch(url + '/console/say', request)
          .then(function(response) { if (!response.ok) throw new Error('Status: ' + response.status); })
          .catch(logger.error);
      });
  };
}
