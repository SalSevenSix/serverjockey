#!/usr/bin/env python3

import sys
from random import randint
from time import sleep


def p(line):
    print(line, flush=True)


def main():
    p('### Initialising')
    p('1599635857306 versionNumber=40.43 demo=false')
    sleep(1)
    p('server is listening on port 16261')
    sleep(1)
    p('Server Steam ID 90138653263221765')
    p('### *** SERVER STARTED ***')
    players = ['MrGoober', 'StabMasterArson', 'YouMadNow']
    for player in players:
        sleep(1)
        p('### Player {} has joined the server'.format(player))
        p("znet: Java_zombie_core_znet_SteamGameServer_BUpdateUserData '{}' id={}".format(player, randint(1, 1000)))

    running = True
    while running:
        line = sys.stdin.readline()
        line = line.strip()
        p('### Received STDIN: {}'.format(line))
        p(line)
        if line == 'players':
            p('### some garbage')
            p('### more garbage')
            p('Players connected ({}):'.format(len(players)))
            for player in players:
                p('-{}'.format(player))
            p('')
            p('### some more junk')
        elif line == 'showoptions':
            p('List of Server Options:')
            p('* PvP=False')
            p('* MaxPlayerCount=16')
            p('* ModsList=better_guns,hydro,survivor_radio')
            p('* SaveOnExit=True')
            p('* DayLength=12')
            p('* ServerWelcomeMessage=Welcome to PZ test-script.sh <LINE> Enjoy testing!')
            p('end')
        elif line.find('kickuser') != -1:
            found = None
            for player in players:
                if line.find(player) != -1:
                    found = player
            if found:
                players.remove(found)
        elif line == 'quit':
            p('### shutting down')
            p('### messaging players')
            sleep(1)
            p('### goodbye')
            return
        else:
            p('### NOOP')


if __name__ == '__main__':
    main()
