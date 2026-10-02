import json
import os
import re
import shutil
import sys
from datetime import datetime, timedelta
from html import escape

from threading import Thread

import webview
from platformdirs import PlatformDirs


class CardApi:
    def __init__(self, card):
        self._card = card
        self._window = None

    def close(self):
        for window in webview.windows:
            window.destroy()

    def punch(self):
        puncher = getattr(self._card, "puncher", None)
        if puncher is None:
            return {"ok": False, "kind": "error", "msg": "打卡功能不可用"}
        try:
            return puncher.punch()
        except Exception as e:
            return {"ok": False, "kind": "error", "msg": f"打卡出错：{e}"}

    def refresh(self):
        if self._window is not None:
            self._window.load_html(self._card.read_html())


class Card:
    APP_NAME = "LuoguDailyPunch"
    CONFIG_PATH = os.path.join(PlatformDirs(APP_NAME).user_data_dir, "config.json")
    PLACEHOLDER_RE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)\$")

    @staticmethod
    def base_dir():
        compiled = globals().get("__compiled__")
        if compiled is not None:
            argv0 = getattr(compiled, "original_argv0", None) or sys.argv[0]
            return os.path.dirname(os.path.abspath(argv0))
        if getattr(sys, "frozen", False):
            exe = sys.argv[0]
            if os.path.dirname(exe) == "":
                exe = shutil.which(exe) or exe
            return os.path.dirname(os.path.abspath(exe))
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @staticmethod
    def html_path():
        return os.path.join(Card.base_dir(), "ui", "kanban.html")

    def __init__(self, config, puncher=None):
        self.config = config
        self.puncher = puncher

    def pick(self, res, key, index=0, default="-"):
        values = res.get(key) or []
        if index < len(values):
            value = str(values[index]).strip()
            if value:
                return value
        return default

    def items(self, res, key):
        return [str(v).strip() for v in (res.get(key) or []) if str(v).strip()]

    def fill_column(self, names, tips, empty_phrase):
        if not names:
            return [empty_phrase, "", "", ""]
        return [
            names[0],
            tips[0] if tips else "",
            names[1] if len(names) > 1 else "",
            tips[1] if len(tips) > 1 else "",
        ]

    def build_data(self, config):
        res = config.get("lastPunchRes") or {}
        now = datetime.now()
        punch_ts = config.get("lastPunchTime")
        punch_dt = datetime.fromtimestamp(punch_ts) if punch_ts else None

        username = self.pick(res, "username")

        good1, good1_tip, good2, good2_tip = self.fill_column(
            self.items(res, "goodThings"), self.items(res, "goodTips"), "诸事不宜"
        )
        bad1, bad1_tip, bad2, bad2_tip = self.fill_column(
            self.items(res, "badThings"), self.items(res, "badTips"), "诸事皆宜"
        )

        data = {
            "top_date": f"{now.month}月{now.day}日 周{'一二三四五六日'[now.weekday()]}",
            "username": username,
            "avatar": username[:1],
            "grade": self.pick(res, "punchRes"),
            "fortune_desc": "",
            "punch_date": punch_dt.strftime("%Y-%m-%d") if punch_dt else "-",
            "punch_time": punch_dt.strftime("%H:%M") if punch_dt else "--:--",
            "status": "已打卡" if punch_dt and punch_dt.date() == now.date() else "未打卡",
            "punched": "1" if punch_dt and punch_dt.date() == now.date() else "0",
            "streak": "-",
            "total": "-",
            "good1": good1,
            "good1_tip": good1_tip,
            "good2": good2,
            "good2_tip": good2_tip,
            "bad1": bad1,
            "bad1_tip": bad1_tip,
            "bad2": bad2,
            "bad2_tip": bad2_tip,
        }

        for i in range(7):
            day = now - timedelta(days=i)
            data[f"date{i + 1}"] = day.strftime("%m-%d")
            data[f"grade{i + 1}"] = (
                data["grade"] if punch_dt and day.date() == punch_dt.date() else "-"
            )
        return data


    def render(self, html_text):
        data = self.build_data(self.config)
        return self.PLACEHOLDER_RE.sub(
            lambda m: m.group(0) if m.group(1) not in data else escape(str(data[m.group(1)])),
            html_text,
        )

    def read_html(self):
        with open(self.html_path(), "r", encoding="utf-8") as f:
            return self.render(f.read())

    def showCard(self):
        api = CardApi(self)
        window = webview.create_window(
            '卡片',
            html=self.read_html(),  # 或你的前端构建产物
            frameless=True,
            easy_drag=True,
            js_api=api,
            width=540,
            height=360,
            resizable=False,   # 无边框窗口通常不可调整大小
            on_top=True        # 卡片常需要置顶
        )
        api._window = window
        webview.start(http_server=True)


if __name__ == "__main__":
    card = Card({})
    with open(card.CONFIG_PATH, "r", encoding="utf-8") as f:
        card.config = json.load(f)
    card.showCard()
