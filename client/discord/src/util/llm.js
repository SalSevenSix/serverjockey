import OpenAI from 'openai';
import * as util from './util.js';
import * as logger from './logger.js';

async function requestChatCompletion(api, config, gamename, messages, input) {
  let content = null;
  if (messages.length === 0 && config.system) {
    content = config.system.replaceAll('{gamename}', gamename);
    messages.push({ role: 'system', content: content });
  }
  if (config.user) {
    content = config.user.replaceAll('{gamename}', gamename);
    content = content.replace('{content}', util.arrayToText(input));
  } else {
    content = util.arrayToText(input);
  }
  messages.push({ role: 'user', content: content });
  const request = { model: config.model, messages: messages };
  if (config.temperature || config.temperature == 0) { request.temperature = parseFloat(config.temperature); }
  const response = await api.chat.completions.create(request);
  const choice = response && response.choices && response.choices.length && response.choices[0].message
    ? response.choices[0] : null;
  if (choice && choice.message.content && (!choice.finish_reason || choice.finish_reason === 'stop')) {
    messages.push(choice.message);
    return choice.message.content;
  }
  if (choice && choice.finish_reason) {
    if (choice.finish_reason === 'length') { messages.length = 0; }  // Reset whole conversation
    else { messages.pop(); }  // Just remove the last input
    return '⛔ Request refused, reason: ' + choice.finish_reason;
  }
  return '⛔ Invalid response\n```\n' + JSON.stringify(response, null, 2) + '\n```';
}

function nullChatCompletion(message) {
  return function() {
    return { request: async function() { return message; } };
  };
}

const noApi = nullChatCompletion('⛔ AI Client not configured for use');
const noFeature = nullChatCompletion('⛔ This AI feature is not configured');

function buildChatCompletion(api, config) {
  if (!config || !config.model) return noFeature;
  return function(gamename) {
    const [self, messages] = [{}, []];
    let [last, busy] = [0, false];
    self.reset = function() {
      messages.length = 0;
    };
    self.request = async function(input) {
      if (busy) return '🤔 *AI is thinking!*';
      busy = true;
      if (Date.now() - last > 420000) { self.reset(); }  // 7 minute memory
      return await requestChatCompletion(api, config, gamename, messages, input)
        .catch(function(error) {
          logger.error(error);
          self.reset();
          return '⛔ AI Client ' + error.toString();
        })
        .finally(function() {
          [last, busy] = [Date.now(), false];
        });
    };
    return self;
  };
}

export function newClient(config) {
  const client = { newChatlog: noApi, newChatbot: noApi };
  if (config && config.baseurl && config.apikey) {
    const api = new OpenAI({ baseURL: config.baseurl, apiKey: config.apikey });
    logger.info('LLM Client initialised on endpoint ' + config.baseurl);
    client.newChatlog = buildChatCompletion(api, config.chatlog);
    client.newChatbot = buildChatCompletion(api, config.chatbot);
  } else {
    logger.info('LLM Client not configured');
  }
  return client;
}
