import OpenAI from 'openai';
import * as cutil from 'common/util/util';
import * as logger from './logger.js';

function staticResponse(delay, text) {
  return async function() {
    if (delay) { await cutil.sleep(delay); }
    return text;
  };
}

const noApi = staticResponse(1000, '⛔ LLM not configured for use');
const noFeature = staticResponse(1000, '⛔ This feature is not configured');
const tooLarge = staticResponse(1000, '⛔ Request too large');

async function requestChatCompletion(api, config, { input, gamename }) {
  const request = { model: config.model, messages: [] };
  config.messages.forEach(function(message) {
    if (!message) { message = 'user'; }
    if (cutil.isString(message)) {
      if (cutil.isString(input)) { input = [input]; }
      input.forEach(function(line) {
        if (Array.isArray(line)) { line = line.join('\n'); }
        request.messages.push({ role: message, content: line });
      });
    } else {
      if (gamename) { message.content = message.content.replaceAll('{gamename}', gamename); }
      request.messages.push(message);
    }
  });
  if (config.maxtokens) {
    const tokens = 2 * request.messages.reduce(function(t, m) { return t + m.content.split(' ').length; }, 0);
    if (tokens > config.maxtokens) return await tooLarge();
  }
  if (config.temperature) { request.temperature = config.temperature; }
  // TODO maybe set maxtoken in request?
  const response = await api.chat.completions.create(request);
  let valid = response && response.choices && response.choices.length;
  valid &&= response.choices[0].message && response.choices[0].message.content;
  if (!valid) return '⛔ Invalid response\n```\n' + JSON.stringify(response, null, 2) + '\n```';
  return response.choices[0].message.content;
}

function buildChatCompletion(api, config) {
  if (!config || !config.model || !config.messages) return noFeature;
  return async function(data) { return await requestChatCompletion(api, config, data); };
}

export function newClient(config) {
  const client = { chatlog: noApi, chatbot: noApi };
  if (config && config.baseurl && config.apikey) {
    const api = new OpenAI({ baseURL: config.baseurl, apiKey: config.apikey });
    logger.info('LLM Client initialised on endpoint ' + config.baseurl);
    client.chatlog = buildChatCompletion(api, config.chatlog);
    client.chatbot = buildChatCompletion(api, config.chatbot);
  } else {
    logger.info('LLM Client not configured');
  }
  return client;
}
