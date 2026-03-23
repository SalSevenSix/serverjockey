import OpenAI from 'openai';
import { tavily } from '@tavily/core';
import * as cutil from 'common/util/util';
import { emojis } from '../util/literals.js';
import * as util from '../util/util.js';
import * as logger from '../util/logger.js';

/* eslint-disable complexity */
async function requestChatCompletion(api, config, gamename, messages, input, tvly) {
  input = util.arrayToText(input);
  let content = null;
  if (messages.length === 0 && config.system) {
    content = config.system.replaceAll('{gamename}', gamename);
    messages.push({ role: 'system', content: content });
  }
  if (tvly && messages.length < 2) {
    const search = await tvly.search(gamename + ' ' + input, { searchDepth: 'advanced', maxResults: 5 });
    if (search && search.results && search.results.length) {
      content = 'Here are some online search results to help with the user request...\n\n';
      content += search.results.map(function(result) {
        return '**Title:** ' + result.title + '\n**Content:** ' + result.content;
      }).join('\n\n');
      messages.push({ role: 'system', content: content });
    }
  }
  if (config.user) {
    content = config.user.replaceAll('{gamename}', gamename);
    content = content.replace('{content}', input);
  } else {
    content = input;
  }
  messages.push({ role: 'user', content: content });
  const request = { model: config.model, messages: messages };
  if (config.temperature || config.temperature == 0) { request.temperature = parseFloat(config.temperature); }
  const response = await api.chat.completions.create(request);
  const choice = response && response.choices && response.choices.length && response.choices[0].message
    ? response.choices[0] : null;
  if (choice && choice.message.content && (!choice.finish_reason || choice.finish_reason === 'stop')) {  // Success
    messages.push(choice.message);
    content = choice.message.content;
  } else if (choice && choice.finish_reason) {  // Request refused
    if (choice.finish_reason === 'length') { messages.length = 0; }  // Reset whole conversation
    else { messages.pop(); }  // Just remove the last input
    content = emojis.error + ' Request refused, reason: ' + choice.finish_reason;
  } else {  // Serious error
    messages.length = 0;
    content = emojis.error + ' Invalid response\n```\n' + JSON.stringify(response, null, 2) + '\n```';
  }
  return content;
}
/* eslint-enable complexity */

function nullChatCompletion(message) {
  return function() {
    return {
      avatar: function() { return emojis.robot; },
      reset: cutil.fNoop,
      request: async function() { return message; }
    };
  };
}

const noApi = nullChatCompletion(emojis.error + ' AI Client not configured for use');
const noFeature = nullChatCompletion(emojis.error + ' This AI feature is not configured');

function buildChatCompletion(api, avatarEmoji, config, tvly = null) {
  if (!config || !config.model) return noFeature;
  return function(gamename) {
    const [self, messages] = [{}, []];
    let [last, busy] = [0, false];
    self.avatar = function() { return avatarEmoji; };
    self.reset = function() { messages.length = 0; };
    self.request = async function(input) {
      if (busy) return emojis.thinking + ' *AI is busy!*';
      busy = true;
      if (Date.now() - last > 420000) { self.reset(); }  // 7 minute memory
      return await requestChatCompletion(api, config, gamename, messages, input, tvly)
        .catch(function(error) {
          logger.error(error);
          self.reset();
          return emojis.error + ' AI Client ' + error.toString();
        })
        .finally(function() {
          [last, busy] = [Date.now(), false];
        });
    };
    return self;
  };
}

function pickAvatarEmoji(apikey) {
  if (apikey.length < 4) return emojis.robot;
  let result = apikey.slice(-3).split('');
  result = result.map(function(char) { return char.charCodeAt(0); });
  result = result[0] * result[1] + result[2];
  result = emojis.avatars[result % emojis.avatars.length];
  return result;
}

export function newClient(config) {
  const client = { newChatlog: noApi, newChatbot: noApi };
  if (config && config.baseurl && config.apikey) {
    const api = new OpenAI({ baseURL: config.baseurl, apiKey: config.apikey });
    const tvly = config.tvlykey ? tavily({ apiKey: config.tvlykey }) : null;
    logger.info('LLM Client (' + (tvly ? 'with' : 'without') + ' Tavily search) initialised ' + config.baseurl);
    const avatarEmoji = pickAvatarEmoji(config.apikey);
    client.newChatlog = buildChatCompletion(api, avatarEmoji, config.chatlog);
    client.newChatbot = buildChatCompletion(api, avatarEmoji, config.chatbot, tvly);
  } else {
    logger.info('LLM Client not configured');
  }
  return client;
}
