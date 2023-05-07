#!/usr/bin/python3

import csv
import requests
import datetime
import json
from rich.console import Console
from rich.table import Column, Table
from config import *

class SteamAPI:
    def __init__(self, api_key:str):
        self.api_key = api_key
        self.url = "http://api.steampowered.com"

    def get_friend_ids(self, steam_id:str) -> list[str]:
        #获取用户的好友ID列表
        response = requests.get(f"{self.url}/ISteamUser/GetFriendList/v0001/?key={self.api_key}&steamid={steam_id}$relationship=friend")
        print(f"friends:{response}")
        friends = json.loads(response.text)['friendslist']['friends']
        friend_ids = [friend['steamid'] for friend in friends]
        print(f"friend_ids:{friend_ids}")
        return friend_ids

    def get_friend_info(self, friend_ids:list[str], online_flag = 1) -> list[dict]:
        #获取好友信息
        friend_info = []
        friend_id = ','.join(friend_ids)
        #for friend_id in friend_ids:
        if friend_id:
            response = requests.get(f"{self.url}/ISteamUser/GetPlayerSummaries/v0002/?key={self.api_key}&steamids={friend_id}")
            print(f"friend_id{friend_id}")
            print(f"friend_info{response}")
            #friend_data = json.loads(response.text)["response"]["players"][0]
            friend_datas = json.loads(response.text)["response"]["players"]
            for friend_data in friend_datas:
            #判断是否筛选在线好友
                if online_flag:
                    #判断好友是否在线
                    if friend_data['personastate'] > 0:
                        #判断好友是否在游戏中
                        if 'gameextrainfo' in friend_data:
                            friend_data['status'] = friend_data['gameextrainfo']
                        #判断好友是否在steam
                        elif friend_data['personastate'] == 1:
                            friend_data['status'] = 'Online'
                        #判断好友是否离开
                        else:
                            friend_data['status'] = 'Leave'
                        friend_info.append(friend_data)
                    else:
                        continue
                else:
                    friend_info.append(friend_data)
                print(f"friend_data{friend_data}")
            #time.sleep(1)
        return friend_info

    def get_played_info(self, friend_id:str) -> list[dict]:
        #获取游戏时长
        game_info = []
        response = requests.get(f"{self.url}/IPlayerService/GetRecentlyPlayedGames/v0001/?key={self.api_key}&steamid={friend_id}")
        game_data = json.loads(response.text)["response"]
        game_info.append(game_data)
        return game_info

    def get_owned_games(self, steam_id:str) -> dict:
        #获取游戏信息
        response = requests.get(f"{self.url}/IplayerService/GetOwnedGames/v0001/?key={self.api_key}&steamid={steam_id}&format=json&include_appinfo=1&include_played_free_games=1")
        game_data = json.loads(response.text)["response"]
        return game_data


class SteamFriendInfo:
    def __init__(self, steam_id:str, steam_api:SteamAPI):
        self.steam_id = steam_id
        self.steam_api = steam_api

    def get_friends_info(self) -> list[dict]:
        friend_ids = self.steam_api.get_friend_ids(self.steam_id)
        friend_info = self.steam_api.get_friend_info(friend_ids)
        return friend_info

    def get_table(self, friend_info:list[dict]) -> Table:
        #生成显示在线好友列表
        #table = Table[show_header = True, header_style="bold magenta"]
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Steam ID",justify="center")
        table.add_column("昵称",justify="center")
        table.add_column("状态",justify="center")
        table.add_column("两周游戏时长",justify="center")
        print(f"friend_info{friend_info}")
        for friend in friend_info:
            playtime = 0
            played_time = self.steam_api.get_played_info(friend['steamid'])[0]['games']
            for played in played_time:
                playtime += played["playtime_2weeks"]
            table.add_row(friend['steamid'], friend['personaname'], friend['status'], str(playtime))
        return table

    def save_play_record(self):
        print("Save play record")
        friend_ids = [""]
        friend_info = self.steam_api.get_friend_info(friend_ids,0)
        with open('GameSummary.csv', 'a', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            for friend in friend_info:
                played_time = self.steam_api.get_played_info(friend['steamid'])[0]
                csvData = (datetime.date.today(), friend['steamid'], friend['personaname'], played_time['total_count'])
                for played in played_time['games']:
                    csvData = csvData + (played['name'],played['playtime_forever'])
                csvwriter.writerow(csvData)

def main():
    steam_api_key = STEAM_API_KEY
    steam_api = SteamAPI(steam_api_key)
    steam_id = STEAM_UID
    #在终端打印online friend info on steam
    #friend_info = SteamFriendInfo(steam_id, steam_api).get_friends_info()
    #table = SteamFriendInfo(steam_id, steam_api).get_table(friend_info)
    #console = Console()
    #console.print(table)
    #记录指定用户steam最近两周游玩时长
    #record = SteamFriendInfo(steam_id, steam_api).save_play_record()
    #获取拥有游戏信息
    print(steam_api.get_owned_games(steam_id))

if __name__ == "__main__":
    main()
