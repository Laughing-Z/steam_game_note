#!/usr/bin/python3
import requests
from steam_game_note.getfriend import *
import datetime
from steam_game_note.config import *

class NotionAPI:
    def __init__(self,api_key,page_id):
        self.api_key = api_key
        self.page_id = page_id
        self.database_url = "https://api.notion.com/v1/databases/"
        self.page_url = "https://api.notion.com/v1/pages"
        self.headers = {
            "Authorization": "Bearer " + api_key,
            "accept": "application/json",
            "Notion-Version": "2022-06-28",
            "content-type": "application/json"
        }
        self.new_database_id = NOTION_DATABASE_ID

    def convert_minutes_to_hours(self,minutes):
        hours = minutes // 60
        remaining_minutes = minutes % 60
        return hours, remaining_minutes
    
    def create_notion_database(self,status):
        if status == '0':
            return NOTION_DATABASE_ID
        #创建数据库
        properties = {
            "id": {"title": {}},
            "appid": {"number": {},},
            "icon": {"files": {}},
            "game_name": {"rich_text": {}},
            "playtime_forever": {"rich_text": {}},
            "playtime_windows_forever": {"number":{},},
            "playtime_mac_forever": {"number": {},},
            "playtime_linux_forever": {"number": {},},
            "rtime_last_played": {"rich_text": {}},
            "cover": {"files": {}}
        }
        data = {
            "parent": {"page_id": self.page_id},
            "title": [{"type": "text", "text": {"content": 'STEAM_OWNED_GAMES_TEST1'}}],
            "properties": properties,
        }
        response = requests.post('https://api.notion.com/v1/databases', headers=self.headers, json=data)
        if response.status_code == 200:
            self.new_database_id = response.json()['id']
            print(f"New database created with ID: {self.new_database_id}")
            linew = ''
            with open('./config.py','r') as cf:
                lines = cf.read()
                lines = lines.replace('notion_database_id',self.new_database_id)
                lines = lines.replace('-','')
                lines = lines.replace('True','0')
            with open('./config.py','w') as cf:
                cf.write(lines)
            return self.new_database_id
        else:
            print("Error creating database:", response.json())

    def query_notion_database(self):
        #查询数据库信息
        print(NOTION_DATABASE_ID)
        response = requests.post(self.database_url + self.new_database_id + "/query", headers=self.headers)
        if response.status_code == 200:
            result = response.json()
            all_results = result['results']
            #免费用户每次查询一百条，需要多次查询
            while result.get('has_more'):
                cursor = result['next_cursor']
                result = requests.post(self.database_url + self.new_database_id + "/query",headers=self.headers,json={"start_cursor":cursor}).json()
                all_results += result["results"]
            return all_results
        else:
            print("Error query database")
            return False
    
    def get_database_exist(self,all_result=False):
        #获取已存在appid和游戏时长
        result = self.query_notion_database()
        if all_result:
            return result
        if result:
            #print(result)
            exist_appid = {}
            for i in result:
                exist_appid[i['properties']['appid']['number']] = i['properties']['playtime_windows_forever']['number']
            return exist_appid
        else:
            return False
    
    def insert_notion_page(self):
        #获取steam数据
        steam_api_key = STEAM_API_KEY
        steam_id = STEAM_UID
        steam_api = SteamAPI(steam_api_key)
        result = steam_api.get_owned_games(steam_id)
        #数据库中插入数据
        game_count = 0
        save_appid = self.get_database_exist()
        print(save_appid)
        for i in result['games']:
            game_count += 1
            #获取steam游戏标题封面
            cover_url = "https://cdn.cloudflare.steamstatic.com/steam/apps/" + str(i['appid']) + "/header.jpg"
            hours, remaining_minutes = self.convert_minutes_to_hours(int(i['playtime_forever']))
            body = {
                "parent":{
                    "type": "database_id",
                    "database_id": self.new_database_id
                },
                "properties":{
                    "id":{
                        "title": [{"type": "text", "text": {"content": str(game_count)}}]
                    },
                    "appid":{
                        "type": "number",
                        "number":int(i['appid'])
                    },
                    "icon":{
                        "type": "files",
                        "files": [{"name":str(i['name'])+'.png',"external":{"url":"http://media.steampowered.com/steamcommunity/public/images/apps/" + str(i['appid']) + "/" + str(i['img_icon_url']) + ".jpg"}}]
                    },
                    "game_name":{
                        "type": "rich_text",
                        "rich_text":[{"text":{"content":str(i['name'])}}],
                    },
                    "playtime_forever":{
                        "type": "rich_text",
                        "rich_text":[{"text":{"content":str(hours)+"时"+str(remaining_minutes)+"分"}}],
                    },
                    "playtime_windows_forever":{
                        "type": "number",
                        "number": int(i['playtime_windows_forever']),
                    },
                    "playtime_mac_forever":{
                        "type": "number",
                        "number": int(i['playtime_mac_forever']),
                    },
                    "playtime_linux_forever":{
                        "type": "number",
                        "number": int(i['playtime_mac_forever']),
                    },
                    "rtime_last_played":{
                        "type": "rich_text",
                        "rich_text": [{ "text":{"content":str(datetime.datetime.fromtimestamp(i['rtime_last_played']))}}],
                    },
                     "cover":{
                        "type": "files",
                        "files": [{"name":str(i['name'])+'.png',"external":{"url":cover_url}}]
                    },
                }
            }

            #print(i['appid'],i['playtime_forever'])
            game_name = i['name']
            #插入新游戏数据
            if not save_appid or i['appid'] not in save_appid:
                response = requests.post(self.page_url, json=body, headers=self.headers)
                print(f'{game_name} Insert Success')
            #更新游戏数据
            elif i['playtime_windows_forever'] != save_appid[i['appid']]:
                print("Start")
                pages = self.get_database_exist(True)
                for page in pages:
                    if page['properties']['appid']['number'] == i['appid']:
                        page['properties']['playtime_windows_forever']['number'] = i['playtime_windows_forever']
                        page['properties']['playtime_forever']['rich_text'][0]['text']['content'] = str(hours)+"时"+str(remaining_minutes)+"分"
                        page['properties']['rtime_last_played']['rich_text'][0]['text']['content'] = str(datetime.datetime.fromtimestamp(i['rtime_last_played']))
                        response = requests.patch(self.page_url+ "/" +str(page['id'].replace("-","")),headers=self.headers,json=page)
                        if response.status_code == 200:
                            print(f"Update {game_name} Success")
                        break
            else:
                if game_count == result['game_count']:
                    print('Already Exist Or No Update')
                continue

def main():
    notion_api_key = NOTION_API_KEY
    notion_page_id = NOTION_PAGE_ID
    create_status = NOTION_DATABASE_STATUS
    notion = NotionAPI(notion_api_key,notion_page_id)
    notion_database_id = notion.create_notion_database(create_status)
    notion.insert_notion_page()


if __name__ == "__main__":
    main()
