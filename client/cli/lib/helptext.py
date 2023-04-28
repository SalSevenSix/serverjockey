# ALLOW lib.util


def epilog() -> str:
    return '''
examples:
  serverjockey_cmd.pyz -c use:myserver server-start
  sudo serverjockey_cmd.pyz -t upgrade

tasks:
  upgrade                | Upgrade ServerJockey to latest version
  adduser:<name>,<port>  | Add a new ServerJockey service user
                         | called <name> with webapp using <port>
  userdel:<name>         | Delete ServerJockey user and home folder
  service-status:<name>  | Show service status, user <name> optional
  service-start:<name>   | Start service, user <name> optional
  service-stop:<name>    | Stop service, user <name> optional
  service-enable:<name>  | Enable service, user <name> optional
  service-disable:<name> | Disable service, user <name> optional
  uninstall              | Uninstall ServerJockey and delete default user

commands:
  showtoken         | Show webapp url and login token
  system            | Show system information
  report            | Show report on all instances
  modules           | List the modules (supported game servers)
  instances         | List the instances (game servers)
  use:<instance>    | Set the current <instance> to use
  create:<instance>,<module>  | Create a new instance called <instance>
                              | of type <module>
  install-runtime:<version>   | Install game server on current instance,
                              | <version> is optional
  runtime-meta      | Show meta information about the installed runtime
                    | Error will be shown if no runtime is installed
  server            | Show the server status
  server-daemon     | Start the server with automatic restart
                    | if it stops or crashes
  server-start      | Start the server
  server-restart    | Stop then immediately start the server
  server-stop       | Stop the server
  players           | List the players currently in-game
  world-broadcast:"<message>" | Broadcast <message> to all players in-game
                              | Not all modules support this command
  console-send:"<cmd>"        | Send command to the server console
                              | Not all modules support this command
  backup-world:<prunehours>   | Make a backup of the game world, optionally
                              | delete world backups older than <prunehours>
  backup-runtime:<prunehours> | Make a backup of the runtime, optionally
                              | delete runtime backups older than <prunehours>
  wipe-runtime      | Delete the currently installed game server
  wipe-world-all    | Delete all game world data
  wipe-world-save   | Delete only game save, keep config and logs
                    | This command may not be supported on all modules
  log-tail:<lines>  | Get last 100 lines from log file,
                    | or <lines> if provided, up to 100
  log-tail-f        | Get last 10 lines from log then follow additional lines
                    | Use Ctrl-C to exit
  sleep:<seconds>   | Wait and do nothing for <seconds>
  exit-if-down      | Stop processing commands and exit if server is down
  exit-if-up        | Stop processing commands and exit if server is running
  exit-if-players   | Stop processing commands and exit if players are in-game
  exit-if-noplayers | Stop processing commands and exit if no players in-game
  delete            | Delete the current instance
  shutdown          | Shutdown the ServerJockey system
'''
