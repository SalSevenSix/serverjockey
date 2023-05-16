# ALLOW core.* unturned.messaging
from core.util import cmdutil
from core.msg import msgabc
from core.http import httpabc, httprsc
from core.proc import prcext
from core.common import interceptors

_COMMANDS = cmdutil.CommandLines({'send': '{line}'})


def resources(mailer: msgabc.MulticastMailer, resource: httpabc.Resource):
    r = httprsc.ResourceBuilder(resource)
    r.reg('s', interceptors.block_not_started(mailer))
    r.psh('console')
    r.put('help', _ConsoleHelpHandler())
    r.put('{command}', prcext.ConsoleCommandHandler(mailer, _COMMANDS), 's')


class _ConsoleHelpHandler(httpabc.GetHandler):

    def handle_get(self, resource, data):
        return '''UNTURNED CONSOLE COMMANDS
Admin [SteamID | Player]
Admins
Airdrop
AllowP2PRelay
Animal [SteamID | Player]/[AnimalID]
Ban [SteamID | Player]/[Reason]/[Duration]
Bans
Bind [IP]
Chatrate [Number]
Cheats
Cycle [Number]
Day
Debug
EffectUI [EffectID]
Experience [SteamID | Player]/[Experience]
Filter
Flag [SteamID | Player]/[Flag]/[Value]
GameMode [Class Name]
Give [SteamID | Player]/[ItemID]/[Amount]
Gold
GSLT [Login Token]
Hide_Admins
Kick [SteamID | Player]/[Reason]
Kill [SteamID | Player]
Loadout [SkillsetID]/[ItemID]/[ItemID]/...
Log [Chat Y/N]/[Join/Leave Y/N]/[Death Y/N]/[Anticheat Y/N]
Map [Level]
MaxPlayers [Number]
Mode [Easy | Normal | Hard]
Modules
Name [Text]
Night
Owner [SteamID]
Password [Text]
Permit [SteamID]/[Tag]
Permits
Perspective [First | Third | Both | Vehicle]
Players
Port [Number]
PvE
Quest [SteamID | Player]/[Quest]
Queue_Size [Number]
Reload [GUID]
Reputation [SteamID | Player]/[Reputation]
ResetConfig
Save
Say [Text]/[R]/[G]/[B]
Slay [SteamID | Player]/[Reason]
Spy [SteamID | Player]
Sync
Teleport [SteamID | Player]/[SteamID | Player | Location]
Time [Number]
Timeout [Number]
Unadmin [SteamID | Player]
Unban [SteamID]
Unpermit [SteamID]
Vehicle [SteamID | Player]/[VehicleID]
Votify [Vote Allowed Y/N]/[Pass Cooldown]/[Fail Cooldown]/[Vote Duration]/[Vote Percentage]/[Players]
Weather [None | Disable | Storm | Blizzard | GUID]
Welcome [Text]/[R]/[G]/[B]
Whitelisted

Use Help {command} to get detailed documentation.
Command output will be shown in the console log.
'''
