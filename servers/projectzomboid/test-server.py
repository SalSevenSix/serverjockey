#!/usr/bin/env python3

import sys
import asyncio
from random import *


async def main():

    print('### Initialising')
    print('1599635857306 versionNumber=40.43 demo=false')
    await asyncio.sleep(1)
    print('server is listening on port 16261')
    await asyncio.sleep(1)
    print('Server Steam ID 90138653263221765')
    print('### *** SERVER STARTED ***')
    players = ['MrGoober', 'StabMasterArson', 'YouMadNow']
    for player in players:
        print('### Player {} has joined the server'.format(player))
        print("znet: Java_zombie_core_znet_SteamGameServer_BUpdateUserData '{}' id={}".format(player, randint(1, 1000)))

    running = True
    while running:
        line = sys.stdin.readline()
        line = line.strip()
        print('### Received STDIN: {}'.format(line))
        print(line)
        if line == 'players':
            print('### some garbage')
            print('### more garbage')
            print('Players connected ({}):'.format(len(players)))
            for player in players:
                print('-{}'.format(player))
            print('')
            print('### some more junk')
        elif line == 'showoptions':
            print('List of Server Options:')
            print('* PvP=False')
            print('* MaxPlayerCount=16')
            print('* ModsList=better_guns,hydro,survivor_radio')
            print('* SaveOnExit=True')
            print('* DayLength=12')
            print('* ServerWelcomeMessage=Welcome to PZ test-script.sh <LINE> Enjoy testing!')
            print('end')
        elif line.find('kickuser') != -1:
            found = None
            for player in players:
                if line.find(player) != -1:
                    found = player
            if found:
                players.remove(found)
        elif line == 'quit':
            print('### shutting down')
            print('### messaging players')
            await asyncio.sleep(1)
            print('### goodbye')
            return
        else:
            print('### NOOP')


if __name__ == '__main__':
    asyncio.run(main())
