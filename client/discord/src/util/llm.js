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
  if (config.maxtokens) {
    const tokens = 2 * messages.reduce(function(t, m) { return t + m.content.split(' ').length; }, 0);
    if (tokens > config.maxtokens) {
      messages.length = 0;
      return '⛔ Request too large';
    }
  }
  const request = { model: config.model, messages: messages };
  if (config.temperature) { request.temperature = config.temperature; }
  console.log(request);  // TODO debug
  const response = await api.chat.completions.create(request);
  let valid = response && response.choices && response.choices.length;
  valid &&= response.choices[0].message && response.choices[0].message.content;
  if (!valid) {
    messages.pop();
    return '⛔ Invalid response\n```\n' + JSON.stringify(response, null, 2) + '\n```';
  }
  content = response.choices[0].message.content;
  messages.push({ role: 'assistant', content: content });
  return content;
}

function nullChatCompletion(message) {
  return function() {
    return { request: async function() { return message; } };
  };
}

const noApi = nullChatCompletion('⛔ LLM not configured for use');
const noFeature = nullChatCompletion('⛔ This feature is not configured');

function buildChatCompletion(api, config) {
  if (!config || !config.model) return noFeature;
  return function(gamename) {
    const [self, messages] = [{}, []];
    let last = 0;
    self.reset = function() {
      messages.length = 0;
    };
    self.request = async function(input) {
      if (Date.now() - last > 420000) { self.reset(); }  // 7 minute memory
      const response = await requestChatCompletion(api, config, gamename, messages, input);
      last = Date.now();
      return response;
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
