import OpenAI from 'openai';
import * as util from './util.js';
import * as logger from './logger.js';

async function requestChatCompletion(api, config, gamename, input) {
  const request = { model: config.model, messages: [] };
  let content = null;
  if (config.system) {
    content = config.system.replaceAll('{gamename}', gamename);
    request.messages.push({ role: 'system', content: content });
  }
  if (config.user) {
    content = config.user.replaceAll('{gamename}', gamename);
    content = content.replace('{content}', util.arrayToText(input));
  } else {
    content = util.arrayToText(input);
  }
  request.messages.push({ role: 'user', content: content });
  if (config.maxtokens) {
    const tokens = 2 * request.messages.reduce(function(t, m) { return t + m.content.split(' ').length; }, 0);
    if (tokens > config.maxtokens) return '⛔ Request too large';
  }
  if (config.temperature) { request.temperature = config.temperature; }
  // TODO maybe set maxtoken in request?
  console.log(request);  // TODO debug
  const response = await api.chat.completions.create(request);
  let valid = response && response.choices && response.choices.length;
  valid &&= response.choices[0].message && response.choices[0].message.content;
  if (!valid) return '⛔ Invalid response\n```\n' + JSON.stringify(response, null, 2) + '\n```';
  return response.choices[0].message.content;
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
    const self = {};
    self.request = async function(input) {
      return await requestChatCompletion(api, config, gamename, input);
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
