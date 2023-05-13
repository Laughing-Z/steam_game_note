#!/usr/bin/python3

from steam_game_note.getfriend import SteamAPI,SteamFriendInfo
from steam_game_note.notion_steam import NotionAPI
import argparse
from steam_game_note.config import *
from rich.console import Console
from rich.table import Column, Table


def main():
    print("Start")
    parser = argparse.ArgumentParser(description='Steam Interface Command')
    parser.add_argument("--friend",action="store_true",help="Print the Steam Online Friend List")
    parser.add_argument("--notion",action="store_true",help="Update the Notion Database")
    options = parser.parse_args()
    if options.friend:
        steam_api = SteamAPI(STEAM_API_KEY)
        friend_info = SteamFriendInfo(STEAM_UID,steam_api).get_friends_info()
        table = SteamFriendInfo(STEAM_UID,steam_api).get_table(friend_info)
        console = Console()
        console.print(table)
    if options.notion:
        notion_api_key = NOTION_API_KEY
        notion_page_id = NOTION_PAGE_ID
        create_status = NOTION_DATABASE_STATUS
        notion = NotionAPI(notion_api_key,notion_page_id)
        notion_database_id = notion.create_notion_database(create_status)
        notion.insert_notion_page()


    #table = SteamFriendInfo(STEAM_UID,STEAM_API_KEY).get_table(friend_info)

if __name__ == "__main__":
    main()
