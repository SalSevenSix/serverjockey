import OpenAI from 'openai';
import * as cutil from 'common/util/util';

const llm = {
  api: null, config: null,

  summarize: async function(transcript) {
    const messages = [];
    llm.config.chatlog.messages.forEach(function(message) {
      if (!message) { message = 'user'; }
      if (cutil.isString(message)) {
        if (cutil.isString(transcript)) { transcript = [transcript]; }
        transcript.forEach(function(line) {
          if (Array.isArray(line)) { line = line.join('\n'); }
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

export function client(contextConfig) {
  if (llm.api) return llm;
  llm.config = contextConfig.LLM_API;
  if (!llm.config || !llm.config.baseurl || !llm.config.apikey) return null;
  if (!llm.config.chatlog || !llm.config.chatlog.model || !llm.config.chatlog.messages) return null;
  llm.api = new OpenAI({ baseURL: llm.config.baseurl, apiKey: llm.config.apikey });
  return llm;
}
