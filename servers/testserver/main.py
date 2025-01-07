import sys
import os
import signal
import threading
import multiprocessing
import time
import math
import json
from random import randint
# ALLOW NONE


def p(line):
    print(line, flush=True)


class InGameTime:
    def __init__(self, interval_seconds: float):
        self._interval_seconds = interval_seconds

    def run(self):
        if self._interval_seconds <= 0.0:
            return
        while True:
            now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            p('### Ingametime ' + now)
            time.sleep(self._interval_seconds)


class CrashAfterDelay:
    def __init__(self, delay_seconds: float):
        self._delay_seconds = delay_seconds

    def run(self):
        if self._delay_seconds > 0:
            time.sleep(self._delay_seconds)
            p('### FATAL error, shutdown')
            time.sleep(0.1)
            os.kill(os.getpid(), signal.SIGTERM)


def dummy_load(seconds: float):
    end = seconds + time.time()
    while time.time() < end:
        for i in range(100000):
            math.pow(2, 10)


def parse_config() -> dict:
    p('Launch args...')
    config = dict(
        players=sys.argv[1], start_speed_modifier=int(sys.argv[2]),
        crash_on_start_seconds=float(sys.argv[3]), ingametime_interval_seconds=float(sys.argv[4]))
    p(json.dumps(config))
    return config


def initialise() -> list:
    p('### Initialising')
    config = parse_config()
    start_speed_modifier = config['start_speed_modifier']
    threading.Thread(target=CrashAfterDelay(config['crash_on_start_seconds']).run, daemon=False).start()
    p('1599635857306 versionNumber=1.8.42')
    time.sleep(0.5 * start_speed_modifier)
    p('public ip: 101.201.301.404')
    time.sleep(0.5 * start_speed_modifier)
    p('server is listening on port: 27001')
    p('Server Steam ID 90138653263221765')
    p('### *** SERVER STARTED ***')
    players = config['players'].split(',')
    for player in players:
        time.sleep(0.2 * start_speed_modifier)
        p(f'### Player {player} has joined the server')
        p(f"znet: Java_zombie_core_znet_SteamGameServer_BUpdateUserData '{player}' id={randint(1, 1000)}")
    threading.Thread(target=InGameTime(config['ingametime_interval_seconds']).run, daemon=True).start()
    return players


# pylint: disable=too-many-branches,too-many-statements
def main() -> int:
    rc, players = -1, initialise()
    while rc == -1:
        line = sys.stdin.readline()
        line = line.strip()
        p(f'### Received STDIN: {line}')
        if line == 'players':
            p('### some garbage')
            p('### more garbage')
            p(f'Players connected ({len(players)}):')
            for player in players:
                p(f'-{player}')
                time.sleep(0.2)
            p('')
            p('### some more junk')
        elif line.startswith('error'):
            p('### ERROR: ' + line[6:])
        elif line.startswith('broadcast'):
            p('### Broadcast "' + line[10:] + '"')
        elif line.startswith('say'):
            parts = line.split(' ')
            p('### Chat ' + parts[1] + ': ' + ' '.join(parts[2:]))
        elif line.startswith('kill'):
            p('### Kill ' + line.split(' ')[-1])
        elif line.startswith('login'):
            player = line.split(' ')[-1]
            players.append(player)
            p(f'### Player {player} has joined the server')
        elif line.startswith('logout'):
            found = None
            for player in players:
                if line.find(player) != -1:
                    found = player
            if found:
                players.remove(found)
                p(f'### Player {found} has left the server')
        elif line == 'restart-warnings':
            p('### server restart after warnings')
        elif line == 'restart-empty':
            p('### server restart on empty')
        elif line.startswith('load'):
            time.sleep(0.25)
            parts = line.split(' ')
            size, seconds = int(parts[1]), float(parts[2])
            with multiprocessing.Pool(size) as process:
                process.map(dummy_load, [seconds] * size)
        elif line == 'quit':
            p('### shutting down')
            p('### messaging players')
            time.sleep(0.3)
            if len(players) > 0:
                p(f'### Player {players.pop()} has left the server')
            time.sleep(0.5)
            if len(players) > 0:
                p(f'### Player {players.pop()} has left the server')
            time.sleep(0.2)
            p('### goodbye')
            rc = 0
        elif line == 'crash':
            p('### FATAL shutting down')
            time.sleep(0.1)
            rc = 1
        else:
            p('### NOOP')
    return rc


if __name__ == '__main__':
    sys.exit(main())
