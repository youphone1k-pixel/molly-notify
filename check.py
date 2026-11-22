#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ตรวจช่อง YouTube หนึ่งรอบ แล้วแจ้งเตือนผ่าน ntfy (ออกแบบให้รันบน GitHub Actions)"""
import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

TOPIC = os.environ.get("NTFY_TOPIC", "").strip()
TEST = os.environ.get("TEST_NOTIFY") == "1"
CHANNELS = [c.strip() for c in Path("channels.txt").read_text(encoding="utf-8").splitlines()
            if c.strip() and not c.startswith("#")]
STATE_FILE = Path("state.json")
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
UA = {"User-Agent": "Mozilla/5.0 (yt-notify)"}


def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()


def notify(title, message, click=""):
    data = {"topic": TOPIC, "title": title, "message": message, "tags": ["tv"]}
    if click:
        data["click"] = click
    req = urllib.request.Request("https://ntfy.sh", data=json.dumps(data).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=30).read()


def main():
    if not TOPIC:
        raise SystemExit("ยังไม่ได้ตั้ง secret ชื่อ NTFY_TOPIC")
    if TEST:
        notify("✅ แจ้งเตือนช่อง MOLLY", "ทดสอบสำเร็จ! ระบบบน GitHub ทำงานได้")
        print("ส่งแจ้งเตือนทดสอบแล้ว")
    state = json.loads(STATE_FILE.read_text(encoding="utf-8")) if STATE_FILE.exists() else {}
    for cid in CHANNELS:
        root = ET.fromstring(fetch("https://www.youtube.com/feeds/videos.xml?channel_id=" + cid))
        name = root.findtext("a:title", default=cid, namespaces=NS)
        first = cid not in state
        seen = set(state.get(cid, []))
        for e in reversed(root.findall("a:entry", NS)):
            vid = e.findtext("yt:videoId", namespaces=NS)
            if vid in seen:
                continue
            seen.add(vid)
            if not first:
                title = e.findtext("a:title", namespaces=NS)
                url = e.find("a:link", NS).attrib["href"]
                print("แจ้งเตือน:", name, "-", title)
                notify("📺 " + name, title, url)
        state[cid] = sorted(seen)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


main()
