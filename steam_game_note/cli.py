#!/usr/bin/python3

from steam_game_note.getfriend import *
import argparse

def main():
    print("Start")
    parser = argparse.ArgumentParser(description='Steam Interface Command')
    parser.add_argument("--friend",action="store_true",help="Print the Steam Online Friend List")

    options = parser.parse_args()
    steam_api = SteamAPI(STEAM_API_KEY)
    friend_info = SteamFriendInfo(STEAM_UID,steam_api).get_friends_info()
    if options.friend:
        table = SteamFriendInfo(STEAM_UID,steam_api).get_table(friend_info)
        console = Console()
        console.print(table)

    #table = SteamFriendInfo(STEAM_UID,STEAM_API_KEY).get_table(friend_info)

if __name__ == "__main__":
    main()
