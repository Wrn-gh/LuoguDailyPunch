import os
import json
import time
import requests
from lxml import etree
from datetime import datetime, timedelta, timezone

URL = "https://www.luogu.com.cn/index/ajax_punch"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0"
}

XPATHS = {
    "username":   "//h2[@style='margin-bottom: 0']/a[@class='lg-fg-bluelight']/text()",
    "punchRes":   "//span[@class='lg-punch-result']/text()",
    "goodThings": "//div[@class='am-u-sm-6 lg-fg-red']/span[@class='lg-bold']/following-sibling::text()[1]",
    "goodTips":   "//div[@class='am-u-sm-6 lg-fg-red']/span[@class='lg-small']/text()",
    "badThings":  "//div[@class='am-u-sm-6'][not(contains(@class,'lg-fg-red'))]/span[@class='lg-bold']/following-sibling::text()[1]",
    "badTips":    "//div[@class='am-u-sm-6'][not(contains(@class,'lg-fg-red'))]/span[@class='lg-small']/text()"
}

BEIJING_TZ = timezone(timedelta(hours=8))


def parse_luogu_fortune(html_text):
    html = etree.HTML(html_text)
    return {k: html.xpath(v) for k, v in XPATHS.items()}


def clean(lst):
    return [x.strip() for x in (lst or []) if x and x.strip()]


def gen_message(parseRes):
    vaild = {
        "username": False,
        "punchRes": False,
        "goodThings": False,
        "goodTips": False,
        "badThings": False,
        "badTips": False,
    }
    for key in vaild:
        if parseRes.get(key) and len(parseRes[key]) > 0:
            vaild[key] = True
    if not any(vaild.values()):
        return "你的运势好像有些复杂", "自己去洛谷看看吧"

    good_things = clean(parseRes.get("goodThings"))
    good_tips = clean(parseRes.get("goodTips"))
    bad_things = clean(parseRes.get("badThings"))
    bad_tips = clean(parseRes.get("badTips"))

    if len(good_things) < 2:
        punch_text = "大凶"
    elif len(bad_things) < 2:
        punch_text = "大吉"
    else:
        punch_text = parseRes["punchRes"][0] if vaild["punchRes"] else "未知运势"

    username = parseRes["username"][0] if vaild["username"] else "未知用户"
    title = f"{punch_text} - {username}的运势"

    message = ""
    if len(good_things) < 2:
        message += "诸事不宜\n"
    else:
        for thing, tip in zip(good_things, good_tips):
            message += f"宜: {thing} [{tip}]\n"
            if message.count("宜:") >= 2:
                break

    if len(bad_things) < 2:
        message += "万事皆宜"
    else:
        for thing, tip in zip(bad_things, bad_tips):
            message += f"忌: {thing} [{tip}]\n"
            if message.count("忌:") >= 2:
                break

    return title, message


def main():
    uid = os.environ["LUOGU_UID"]
    client_id = os.environ["LUOGU_CLIENT_ID"]

    cookies = {"_uid": uid, "__client_id": client_id}
    resp = requests.get(URL, headers=HEADERS, cookies=cookies, timeout=15)
    data = resp.json()

    now_bj = datetime.now(BEIJING_TZ)
    result = {
        "date": now_bj.strftime("%Y-%m-%d"),
        "timestamp": int(time.time()),
        "code": data.get("code"),
        "title": "",
        "message": "",
        "raw": None,
    }

    if data.get("code") == 200:
        parseRes = parse_luogu_fortune(data["more"]["html"])
        title, message = gen_message(parseRes)
        result["title"] = title
        result["message"] = message
        result["raw"] = parseRes
        print(f"[INFO] 打卡成功：{title}\n{message}")
    elif data.get("code") == 201:
        result["title"] = "今天已打卡"
        result["message"] = "一步一个脚印，不能急于求成"
        print("[INFO] 今天已经打过卡了")
    else:
        result["title"] = "打卡失败"
        result["message"] = f"code={data.get('code')}"
        print(f"[ERROR] 打卡失败：{data}")

    os.makedirs("data", exist_ok=True)
    history_file = "data/history.json"
    history = []
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            history = json.load(f)

    history = [h for h in history if h.get("date") != result["date"]]
    history.append(result)
    history = history[-90:]

    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as f:
            f.write(f"## {result['title']}\n\n")
            f.write(f"{result['message']}\n")


if __name__ == "__main__":
    main()
