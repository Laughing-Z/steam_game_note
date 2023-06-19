#!/usr/bin/python3

import csv
import requests
import datetime
import json
import time
from rich.console import Console
from rich.table import Column, Table
from steam_game_note.config import *

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
            response = self.steam_api.get_played_info(friend['steamid'])
            if response == [{}]:
                continue
            played_time = response[0]['games']
            for played in played_time:
                playtime += played["playtime_2weeks"]
            table.add_row(friend['steamid'], friend['personaname'], friend['status'], str(playtime))
        return table

    def print_recently_played(self):
        response = self.steam_api.get_played_info(self.steam_id)
        print(response)
        recently_played = response[0]['games']
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("App ID",justify="center")
        table.add_column("Name",justify="center")
        table.add_column("Playtime 2weeks",justify="center")
        table.add_column("playtime_forever",justify="center")
        for i in range(response[0]['total_count']):
            table.add_row(str(recently_played[i]['appid']),recently_played[i]['name'],str(recently_played[i]['playtime_2weeks']),str(recently_played[i]['playtime_forever']))
        return table

    def game_everyday(self):
        #记录运行时间
        start_time = time.time()
        print("Save game play record everyday")
        #获取今日游戏数据
        result = self.steam_api.get_owned_games(self.steam_id)
        today_game_data = result['games']
        yesterday_result = 0
        everyday_game_data = {}
        #获取昨日游戏数据
        with open('/Users/masho/Downloads/Github/steam_game_note/steam_game_note/gameplay_day/game_yesterday.json','r',encoding='utf-8') as file:
            yesterday_result = json.load(file)
        yesterday_total = yesterday_result['game_count']

        #构建哈希表
        today_game_data_new = {}
        for today_line in today_game_data:
            today_game_data_new[str(today_line['appid'])] = today_line
        yesterday_result_new = {}
        for yesterday_line in yesterday_result['games']:
            yesterday_result_new[str(yesterday_line['appid'])] = yesterday_line
        
        #使用键匹配
        for today_line in today_game_data:
            today_appid = str(today_line['appid'])
            #增加新游戏,且游玩时长有变化（近两周有游玩记录，才会有playtime_2weeks字段）
            if today_appid not in yesterday_result_new:
                if today_line.get("playtime_2weeks",0):
                    everyday_game_data[today_line['name']]  = today_line['playtime_2weeks']
                continue
            #游戏时长更新
            elif today_game_data_new[str(today_line['appid'])]['playtime_windows_forever'] != yesterday_result_new[str(today_line['appid'])]['playtime_windows_forever']:
                everyday_game_data[today_line['name']]  = today_line['playtime_windows_forever'] - yesterday_result_new[str(today_line['appid'])]['playtime_windows_forever']
                continue
            else:
                continue
        print(everyday_game_data)
        #记录每日游戏
        with open('/Users/masho/Downloads/Github/steam_game_note//steam_game_note/gameplay_day/game_everyday.json','a',encoding='utf-8') as file:
            data = {"date":str(datetime.date.today().year) + "-" + str(datetime.date.today().month) + "-" + str(datetime.date.today().day),"games":everyday_game_data}
            print("data"+str(data))
            json.dump(data,file,ensure_ascii=False,indent=4)
            file.write('\n')
        #将今日游戏数据替换昨日游戏数据
        with open ('/Users/masho/Downloads/Github/steam_game_note/steam_game_note/gameplay_day/game_yesterday.json','w',encoding='utf-8') as file:
            json.dump(result,file,ensure_ascii=False,indent=4)
        end_time = time.time()
        # 计算程序运行时长
        duration = end_time - start_time

        # 输出时长（单位为秒）
        print("Program duration:", duration, "seconds")


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
