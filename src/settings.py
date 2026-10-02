import asyncio
import re
import time
from datetime import datetime

import requests
from rich.markup import escape as rich_escape

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Input, Label, Static, Switch

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0",
    "Referer": "https://www.luogu.com.cn/",
}
HOME = "https://www.luogu.com.cn/"


def verify_cookies(uid: str, cid: str):
    """验证 _uid / __client_id 是否有效（只读，不触发打卡）。

    返回 (status, username)，status 取值：
        "valid"        Cookie 有效，username 为洛谷用户名
        "invalid"      拿到了首页但找不到对应账号，视为 Cookie 无效或已过期
        "unreachable"  网络失败或反爬挑战持续，无法验证
    """
    cookies = {"_uid": uid, "__client_id": cid}
    for _ in range(4):
        try:
            resp = requests.get(HOME, headers=HEADERS, cookies=cookies, timeout=12)
        except requests.RequestException:
            return "unreachable", None

        challenge = re.search(r"C3VK=([0-9a-f]+)", resp.text)
        if challenge:
            cookies["C3VK"] = challenge.group(1)
            time.sleep(0.4)
            continue

        if len(resp.text) < 5000:
            continue

        m = re.search(r'"uid":' + re.escape(uid) + r',"name":"([^"]+)"', resp.text)
        if m:
            return "valid", m.group(1)
        return "invalid", None

    return "unreachable", None


class SettingsApp(App):
    TITLE = "洛谷打卡 · 配置"
    SUB_TITLE = "设置用户 UID 与 Cookie 中的 __client_id"

    BINDINGS = [
        Binding("escape", "quit", "退出", show=True),
        Binding("ctrl+s", "save", "保存", show=True),
    ]

    CSS = """
    Screen {
        background: #0f1115;
    }

    Header {
        background: #009be5;
        color: #08151d;
    }

    #main {
        width: 100%;
        max-width: 68;
        height: auto;
        margin: 1 0;
        padding: 0 2;
    }

    #status_panel {
        background: #14171d;
        color: #a5a6ad;
        padding: 1 2;
        border: round #009be5;
        margin-bottom: 1;
        width: 100%;
    }

    Label {
        color: #6e6f77;
        margin-top: 1;
        width: 100%;
    }

    Input {
        margin-top: 0;
        width: 100%;
        background: #14171d;
        color: #ececee;
        border: tall #2a2b30;
    }
    Input:focus {
        border: tall #009be5;
    }

    #cid_row {
        width: 100%;
        height: auto;
    }
    #cid_row Input {
        width: 1fr;
    }
    #cid_row Button {
        margin-left: 1;
        width: auto;
    }

    #silent_row {
        width: 100%;
        height: auto;
        margin-top: 1;
        align-vertical: middle;
    }
    #silent_row Label {
        margin-top: 0;
        width: auto;
        height: 3;
        content-align: left middle;
    }
    #silent {
        margin: 0 1;
        width: auto;
    }
    #silent_hint {
        color: #6e6f77;
    }

    #actions {
        width: 100%;
        height: auto;
        margin-top: 1;
    }
    #actions Button {
        margin-right: 1;
    }
    #save {
        background: #009be5;
        color: #08151d;
    }
    #verify {
        background: #009be5 20%;
        color: #3ab8f0;
    }
    """

    def __init__(self, puncher):
        super().__init__()
        self.puncher = puncher

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical(id="main"):
            yield Static("", id="status_panel")
            yield Label("用户 UID")
            yield Input(placeholder="洛谷用户 UID（纯数字）", id="uid")
            yield Label("__client_id")
            with Horizontal(id="cid_row"):
                yield Input(placeholder="Cookie 中的 __client_id", id="cid", password=True)
                yield Button("显示", id="toggle_cid")
            with Horizontal(id="silent_row"):
                yield Label("静默模式")
                yield Switch(id="silent")
                yield Label("开启后打卡不再弹出提示", id="silent_hint")
            with Horizontal(id="actions"):
                yield Button("保存配置", id="save")
                yield Button("验证", id="verify")
                yield Button("退出", id="quit")
        yield Footer()

    def on_mount(self) -> None:
        cfg = self.puncher.config
        self.query_one("#uid", Input).value = str(cfg.get("UID") or "")
        self.query_one("#cid", Input).value = str(cfg.get("CLIENT_ID") or "")
        self.query_one("#silent", Switch).value = bool(cfg.get("Silent"))
        self._update_status()

    def on_switch_changed(self, event: Switch.Changed) -> None:
        if event.switch.id != "silent":
            return
        self.puncher.set_silent(event.value)
        self._update_status()
        self.notify(
            "已开启静默模式，打卡不再弹出提示" if event.value else "已关闭静默模式",
            severity="information",
        )

    def _update_status(self) -> None:
        uid = self.puncher.config.get("UID") or "未配置"
        cid = self.puncher.config.get("CLIENT_ID") or ""
        lt = self.puncher.config.get("lastPunchTime")
        last = datetime.fromtimestamp(lt).strftime("%Y-%m-%d %H:%M") if lt else "从未"
        silent = "开启" if self.puncher.config.get("Silent") else "关闭"
        self.query_one("#status_panel", Static).update(
            f"[bold cyan]●[/bold cyan] 当前配置   UID: [bold]{rich_escape(str(uid))}[/bold]"
            f"   Client ID: [bold]{'已配置' if cid else '未配置'}[/bold]"
            f"   静默模式: [bold]{silent}[/bold]"
            f"   上次打卡: [bold]{rich_escape(last)}[/bold]"
        )

    def _current_values(self):
        uid = self.query_one("#uid", Input).value.strip()
        cid = self.query_one("#cid", Input).value.strip()
        return uid, cid

    async def _save(self) -> None:
        uid, cid = self._current_values()
        if not uid.isdigit():
            self.notify("UID 必须是纯数字", severity="error")
            return
        if not cid:
            self.notify("Client ID 不能为空", severity="error")
            return
        self.puncher.set_user_info(uid, cid)
        self._update_status()
        self.notify("配置已保存", severity="information")

    async def _verify(self) -> None:
        uid, cid = self._current_values()
        if not uid or not cid:
            self.notify("请先填写 UID 和 Client ID", severity="warning")
            return
        status = self.query_one("#status_panel", Static)
        status.update("[bold cyan]●[/bold cyan] 验证中，请稍候…")
        result_status, username = await asyncio.to_thread(verify_cookies, uid, cid)
        if result_status == "valid":
            self.notify(f"验证成功：{username}", severity="information")
        elif result_status == "invalid":
            self.notify("Cookie 无效或已过期", severity="error")
        else:
            self.notify("验证失败：网络或反爬限制", severity="warning")
        self._update_status()

    async def _toggle_cid(self) -> None:
        cid = self.query_one("#cid", Input)
        cid.password = not cid.password
        self.query_one("#toggle_cid", Button).label = "隐藏" if cid.password else "显示"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "save":
            self.run_worker(self._save())
        elif button_id == "verify":
            self.run_worker(self._verify())
        elif button_id == "toggle_cid":
            self.run_worker(self._toggle_cid())
        elif button_id == "quit":
            self.exit()


def open_settings(puncher) -> None:
    SettingsApp(puncher).run()
