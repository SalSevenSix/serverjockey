import sys
import threading
import time
from random import randint
# ALLOW NONE


def p(line):
    print(line, flush=True)


def ingametime():
    while True:
        p('### Ingametime ' + repr(int(time.time() * 1000.0) + 1))
        time.sleep(80)


def main() -> int:
    p('### Initialising')
    p('1599635857306 versionNumber=1.8.42')
    time.sleep(0.5)
    p('Launch args...')
    for i, arg in enumerate(sys.argv[1:]):
        p('  #' + str(i) + ' ' + str(arg))
    p('public ip: 101.201.301.404')
    time.sleep(0.5)
    p('server is listening on port: 27001')
    p('Server Steam ID 90138653263221765')
    p('### *** SERVER STARTED ***')
    players = ['MrGoober', 'StabMasterArson', 'YouMadNow']
    for player in players:
        time.sleep(0.2)
        p('### Player {} has joined the server'.format(player))
        p("znet: Java_zombie_core_znet_SteamGameServer_BUpdateUserData '{}' id={}".format(player, randint(1, 1000)))
    threading.Thread(target=ingametime, daemon=True).start()

    running = True
    while running:
        line = sys.stdin.readline()
        line = line.strip()
        p('### Received STDIN: {}'.format(line))
        if line == 'players':
            p('### some garbage')
            p('### more garbage')
            p('Players connected ({}):'.format(len(players)))
            for player in players:
                p('-{}'.format(player))
                time.sleep(0.2)
            p('')
            p('### some more junk')
        elif line.find('kick') != -1:
            found = None
            for player in players:
                if line.find(player) != -1:
                    found = player
            if found:
                players.remove(found)
                p('### Player {} has left the server'.format(found))
        elif line == 'quit':
            p('### shutting down')
            p('### messaging players')
            time.sleep(1)
            if len(players) > 0:
                p('### Player {} has left the server'.format(players.pop()))
            time.sleep(0.5)
            if len(players) > 0:
                p('### Player {} has left the server'.format(players.pop()))
            time.sleep(0.5)
            p('### goodbye')
            return 0
        elif line == 'crash':
            p('### FATAL shutting down')
            time.sleep(0.1)
            return 1
        else:
            p('### NOOP')


if __name__ == '__main__':
    sys.exit(main())
