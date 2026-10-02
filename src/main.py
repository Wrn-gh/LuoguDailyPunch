import requests
from lxml import etree

from plyer import notification

import os
import argparse
from platformdirs import PlatformDirs

import json
import time
from datetime import datetime, date

from card import Card

APP_NAME = "LuoguDailyPunch"
appDirs = PlatformDirs(APP_NAME)

DEBUG = False


def popup(title, message):
    notification.notify(
        title=title,
        message=message,
        app_icon=None, 
        timeout=10
    )


class LuoguDailyPuncher:
    url = "https://www.luogu.com.cn/index/ajax_punch"
    base_url = "https://www.luogu.com.cn/"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0"
    }

    xpaths = {
        "username": "//h2[@style='margin-bottom: 0']/a[@class='lg-fg-bluelight']/text()",
        "punchRes": "//span[@class='lg-punch-result']/text()",
        "goodThings": "//div[@class='am-u-sm-6 lg-fg-red']/span[@class='lg-bold']/following-sibling::text()[1]",
        "goodTips": "//div[@class='am-u-sm-6 lg-fg-red']/span[@class='lg-small']/text()",
        "badThings": "//div[@class='am-u-sm-6'][not(contains(@class,'lg-fg-red'))]/span[@class='lg-bold']/following-sibling::text()[1]",
        "badTips": "//div[@class='am-u-sm-6'][not(contains(@class,'lg-fg-red'))]/span[@class='lg-small']/text()"
    }

    configTemplate = {
        "UID": "",
        "CLIENT_ID": "",
        "lastPunchRes": {},
        "PunchRes": [],
        "lastPunchTime": "",
    }

    def __init__(self, configFilePath:str):
        self.configFilePath = configFilePath

        if os.path.exists(self.configFilePath):
            self.load_config()
        else:
            self.config = self.configTemplate
            self.save_config()

    def save_config(self):
        with open(self.configFilePath, "w") as configf:
            json.dump(self.config, configf)
            configf.close()

    def load_config(self):
        with open(self.configFilePath, "r") as configf:
            self.config = json.load(configf)
            configf.close()

    def parse_luogu_fortune(self, html_text: str) -> dict:
        """
        解析luogu打卡返回数据
        args:
            html_text: 返回的html文本, 取response["more"]["html"]字段
        return:
            parseRes: 解析返回结果
        """
        htmlObj = etree.HTML(html_text)

        parseRes = {}
        for xkey in self.xpaths.keys():
            # print("xpath: %s" % self.xpaths[xkey])
            parseRes[xkey] = htmlObj.xpath(self.xpaths[xkey])

        if DEBUG:
            with open(os.path.join(appDirs.user_data_dir, "debug_punch_res.json"), "w", encoding="utf-8") as f:
                json.dump(parseRes, f, ensure_ascii=False, indent=4)
            print("数据已保存到 debug_punch_res.json")

        # print(parseRes)
        return parseRes

    def gen_message(self, parseRes):
        """
        生成通知提示信息
        args:
            parseRes: 解析的信息, 由parse_luogu_fortune提供
        return:
            title, messsage: 表示通知标题与消息
        """
        vaild = {
            "username": False,
            "punchRes": False,
            "goodThings": False,
            "goodTips": False,
            "badThings": False,
            "badTips": False
        }
        for key in ["username", "punchRes", "goodThings", "goodTips", "badThings", "badTips"]:
            if parseRes.get(key) and len(parseRes[key]) > 0:
                vaild[key] = True
        if not any(vaild.values()):
            return "你的运势好像有些复杂", "自己去洛谷看看吧"
        try:
            if len(parseRes["goodThings"]) < 2:
                punchres = "大凶"
            elif len(parseRes["badThings"]) < 2:
                punchres = "大吉"
            else:
                punchres = parseRes["punchRes"][0] if vaild["punchRes"] else "未知运势"
            username = parseRes["username"][0] if vaild["username"] else "未知用户"
            title = punchres + \
            " - " + username + \
            "的运势"

            message = ""
            if len(parseRes["goodThings"]) < 2:
                message += "诸事不宜\n"
            else:
                for i in range(2):
                    mi = "宜: " + parseRes["goodThings"][i] + \
                        " [" + parseRes["goodTips"][i] + "]\n"
                    message += mi
            if len(parseRes["badThings"]) < 2:
                message += "万事皆宜"
            else:
                for i in range(2):
                    mi = "忌: " + parseRes["badThings"][i] + \
                        " [" + parseRes["badTips"][i] + "]\n"
                    message += mi
            return title, message
        except Exception as e:
            print(f"[ERROR] 解析运势数据时出错: {e}")
            return "你的运势好像有些复杂", "自己去洛谷看看吧"

    def punch(self):
        if not self.config["UID"] or not self.config["CLIENT_ID"]:
            print("[ERROR] 未配置用户信息")
            return {"ok": False, "kind": "no_config", "msg": "未配置用户信息，请先运行 lgpunch set"}
        
        # 上次打卡时间
        ltimestamp = self.config["lastPunchTime"]
        ldatetime = datetime.fromtimestamp(ltimestamp).date() if ltimestamp else None
        ndatetime = date.today()
        if ldatetime == ndatetime:
            print("[INFO] 今天你已经打过卡了哦，要一步一个脚印，不能急于求成!")
            return {"ok": False, "kind": "already", "msg": "今天已经打过卡了哦，要一步一个脚印"}

        cookies = {
            "_uid": self.config["UID"],
            "__client_id": self.config["CLIENT_ID"]
        }
        try:
            response = requests.get(url=self.url, headers=self.headers, cookies=cookies, timeout=10)
            jsonObj = response.json()
        except Exception as e:
            print(f"[ERROR] 网络请求失败: {e}")
            return {"ok": False, "kind": "error", "msg": "网络错误，请稍后重试"}

        if jsonObj["code"] == 200:
            print("[INFO] 打卡成功!")
            pRes = self.parse_luogu_fortune(jsonObj["more"]["html"])
            t, m = self.gen_message(pRes)
            self.config["lastPunchRes"] = pRes
            self.config["lastPunchTime"] = time.time()
            pResWithTime = {
                "time": self.config["lastPunchTime"],
                "res": pRes
            }
            history = self.config.setdefault("PunchRes", [])
            if len(history) >= 30:
                history.pop(0)
            history.append(pResWithTime)
            self.save_config()
            popup(t, m)
            return {"ok": True, "kind": "ok", "msg": "打卡成功！"}
        elif jsonObj["code"] == 201:
            print("[INFO] 今天你已经打过卡了哦，要一步一个脚印，不能急于求成!")
            return {"ok": False, "kind": "already", "msg": "今天已经打过卡了哦，要一步一个脚印"}
        else:
            print("[ERROR] 似乎打卡失败了")
            return {"ok": False, "kind": "error", "msg": "打卡失败，请稍后重试"}

    def set_user_info(self, uid, client_id):
        self.config["UID"] = uid
        self.config["CLIENT_ID"] = client_id
        self.save_config()

    def user_info(self):
        print("UID: %s" % self.config["UID"])
        print("CID: %s" % self.config["CLIENT_ID"])

    def punch_info(self):
        t, m = self.gen_message(self.config["lastPunchRes"])
        print(t)
        print(m)
        dtObj = datetime.fromtimestamp(self.config["lastPunchTime"])
        fDate = dtObj.strftime('%Y-%m-%d %H:%M:%S')
        print("Punch Time: %s" % fDate)

    def showCard(self):
        card = Card(self.config, puncher=self)
        card.showCard()

if __name__ == "__main__":
    # 配置文件路径
    config_dir = appDirs.user_data_dir
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, "config.json")

    luogu_daily_puncher = LuoguDailyPuncher(config_path)

    parser = argparse.ArgumentParser(prog="lgpunch", description="Luogu Daily Punch")
    subparser = parser.add_subparsers(dest="command", required=True)

    punch_parser = subparser.add_parser("punch", help="自动打卡")

    set_parser = subparser.add_parser("set", help="设置用户信息")
    set_parser.add_argument("--uid", required=True, help="洛谷用户UID")
    set_parser.add_argument("--cid", required=True, help="Cookie中的__client_id")

    userinfo_parser = subparser.add_parser("userinfo", help="查看用户信息")

    punchres_parser = subparser.add_parser("punchinfo", help="查看打卡信息")

    card_parser = subparser.add_parser("card", help="显示打卡运势卡片")

    args = parser.parse_args()

    if args.command == "punch":
        luogu_daily_puncher.punch()
    elif args.command == "set":
        luogu_daily_puncher.set_user_info(args.uid, args.cid)
        print("[INFO] 用户信息已保存")
    elif args.command == "userinfo":
        luogu_daily_puncher.user_info()
    elif args.command == "punchinfo":
        luogu_daily_puncher.punch_info()
    elif args.command == "card":
        luogu_daily_puncher.showCard()
        