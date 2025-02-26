import * as startup from './commons/startup.js';
import * as servercmds from './commons/servercmds.js';
import * as deploymentcmds from './commons/deploymentcmds.js';
import * as consolecmds from './commons/consolecmds.js';
import * as aliascmds from './commons/aliascmds.js';
import * as rewardcmds from './commons/rewardcmds.js';
import * as activitycmds from './commons/activitycmds.js';

export const [
  startupAll, startupServerOnly,
  server, auto, log,
  getconfig, setconfig, deployment,
  send, say, players,
  alias, reward, activity
] = [
  startup.startupAll, startup.startupServerOnly,
  servercmds.server, servercmds.auto, servercmds.log,
  deploymentcmds.getconfig, deploymentcmds.setconfig, deploymentcmds.deployment,
  consolecmds.send, consolecmds.say, consolecmds.players,
  aliascmds.alias, rewardcmds.reward, activitycmds.activity
];
