import OpenAI from 'openai';
import * as cutil from 'common/util/util';
import * as cstats from 'common/activity/chat';
import * as logger from '../util/logger.js';
import * as util from '../util/util.js';
import * as msgutil from '../util/msgutil.js';

const llm = {
  api: null, config: null,

  init: function(contextConfig) {
    if (llm.api) return true;
    llm.config = contextConfig.LLM_API;
    if (!llm.config || !llm.config.baseurl || !llm.config.apikey) return false;
    if (!llm.config.chatlog || !llm.config.chatlog.model || !llm.config.chatlog.messages) return false;
    llm.api = new OpenAI({ baseURL: llm.config.baseurl, apiKey: llm.config.apikey });
    return true;
  },

  summarize: async function(transcript) {
    const messages = [];
    llm.config.chatlog.messages.forEach(function(message) {
      if (!message) { message = 'user'; }
      if (cutil.isString(message)) {
        transcript.forEach(function(line) {
          messages.push({ role: message, content: line });
        });
      } else {
        messages.push(message);
      }
    });
    if (llm.config.chatlog.maxtokens) {
      const tokens = 2 * messages.reduce(function(t, m) { return t + m.content.split(' ').length; }, 0);
      if (tokens > llm.config.chatlog.maxtokens) {
        await cutil.sleep(1200);  // Allow discord to process waiting emoji first
        return '⛔ Chat transcript too large, try a smaller time range.';
      }
    }
    const request = { messages: messages, model: llm.config.chatlog.model };
    if (llm.config.chatlog.temperature) { request.temperature = llm.config.chatlog.temperature; }
    // TODO maybe set maxtoken in request?
    const response = await llm.api.chat.completions.create(request);
    let valid = response && response.choices && response.choices.length;
    valid &&= response.choices[0].message && response.choices[0].message.content;
    if (!valid) return '⛔ Invalid LLM response\n```\n' + JSON.stringify(response, null, 2) + '\n```';
    return response.choices[0].message.content;
  }
};

function formatHeader(results, tzFlag) {
  const text = [['FROM ' + cutil.shortISODateTimeString(results.meta.atfrom, tzFlag),
    ' TO ' + cutil.shortISODateTimeString(results.meta.atto, tzFlag),
    ' (' + cutil.humanDuration(results.meta.atrange) + ')'].join('')];
  if (results.chat.length === 0) { text.push('No chat found'); }
  return text;
}

async function formatSummary(contextConfig, results, tzFlag) {
  if (!llm.init(contextConfig)) return '⛔ LLM not configured for use';
  const text = formatHeader(results, tzFlag);
  if (results.chat.length === 0) return text;
  results = results.chat.map(function(record) {
    if (!record.player) return null;
    return record.ats + ' ' + record.player + ': ' + record.text;
  });
  results = results.filter(function(line) { return line; });
  results = await llm.summarize(results);
  results = util.textToArray(results);
  text.push(...results);
  return text;
}

function formatVerbose(results, tzFlag) {
  const text = formatHeader(results, tzFlag);
  if (results.chat.length === 0) return text;
  results = results.chat.map(function(record) {
    if (!record.player) return '----- ' + record.at;
    return record.at + ' ' + record.player + ': ' + record.text;
  });
  text.push(...results);
  return text;
}

export function chatlog({ context, httptool, instance, message, data }) {
  if (!msgutil.checkHasRole(message, context.config.ADMIN_ROLE)) return;
  const [baseurl, now] = [context.config.SERVER_URL, new Date()];
  let [tz, atto, atfrom, player, format] = [null, null, null, null, 'VERBOSE'];
  data.forEach(function(arg) {
    if (arg === 'summary') { format = 'SUMMARY'; }
    else if (arg.startsWith('tz=')) { tz = arg.substring(3); }
    else if (arg.startsWith('player=')) { player = arg.substring(7); }
  });
  data.forEach(function(arg) {
    if (arg.startsWith('to=')) {
      atto = arg.substring(3);
      atto = ['LH', 'LD', 'LM', 'TM'].includes(atto)
        ? cutil.presetDate(now, atto, tz).getTime()
        : cutil.parseDateToMillis(atto, tz);
    } else if (arg.startsWith('from=')) {
      atfrom = arg.substring(5);
      atfrom = atfrom && ['d', 'h', 'm', 's'].includes(atfrom.slice(-1).toLowerCase())
        ? 0 - cutil.rangeCodeToMillis(atfrom)
        : cutil.parseDateToMillis(atfrom, tz);
    }
  });
  if (!atto) { atto = now.getTime(); }
  if (!atfrom) { atfrom = atto - 21600000; }
  else if (atfrom < 0) { atfrom = atto + atfrom; }
  if (!tz) { tz = true; }
  httptool.getJson(cstats.queryChats(instance, { atfrom, atto }, player), baseurl)
    .then(function(chatdata) {
      const results = { meta: cstats.extractMeta(chatdata),
        chat: cstats.extractResults(cstats.mergeResults({ chat: chatdata }), tz) };
      if (format === 'VERBOSE') {
        msgutil.sendTextOrFile(message, formatVerbose(results, tz), 'chat');
      } else if (format === 'SUMMARY') {
        msgutil.reactWait(message);
        formatSummary(context.config, results, tz)
          .then(function(text) {
            msgutil.rmReacts(message, msgutil.reactSuccess, logger.error);
            msgutil.sendTextOrFile(message, text, 'chat', 3, false);
          })
          .catch(function(error) {
            msgutil.rmReacts(message, function() { logger.error(error, message); }, logger.error);
          });
      } else {
        msgutil.sendText(message, 'Invalid arguments');
      }
    });
}
