# -*- coding: utf-8 -*-
import sys
import json
import urllib.parse
import requests
import xbmcplugin
import xbmcgui
import xbmcaddon

addon_handle = int(sys.argv[1])
base_url = sys.argv[0]
args = urllib.parse.parse_qs(sys.argv[2][1:])
addon = xbmcaddon.Addon()

# 从设置中读取多个 API 地址
API_URLS = addon.getSetting("api_urls") or ""
API_URLS = [u.strip() for u in API_URLS.split(";") if u.strip()]


def build_url(query):
    return base_url + '?' + urllib.parse.urlencode(query)


def get_json(url):
    try:
        r = requests.get(url, timeout=10)
        return r.json()
    except Exception as e:
        xbmcgui.Dialog().notification("错误", str(e), xbmcgui.NOTIFICATION_ERROR)
        return {}


# ========== 显示所有源 ==========
def list_sources():
    for idx, api in enumerate(API_URLS):
        li = xbmcgui.ListItem(label=f"源 {idx+1} - {api}")
        url = build_url({"mode": "list_categories", "api": api})
        xbmcplugin.addDirectoryItem(addon_handle, url, li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)


# ========== 分类列表 ==========
def list_categories(api_url):
    url = f"{api_url}?ac=class"
    data = get_json(url)
    classes = data.get("class", [])
    for c in classes:
        cid = c.get("type_id")
        name = c.get("type_name")
        li = xbmcgui.ListItem(label=name)
        url = build_url({"mode": "list_videos", "api": api_url, "cid": cid, "pg": 1})
        xbmcplugin.addDirectoryItem(addon_handle, url, li, isFolder=True)

    # 搜索入口
    li = xbmcgui.ListItem(label="[搜索]")
    url = build_url({"mode": "search", "api": api_url})
    xbmcplugin.addDirectoryItem(addon_handle, url, li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)


# ========== 视频列表 ==========
def list_videos(api_url, cid, pg=1, wd=None):
    if wd:
        url = f"{api_url}?ac=videolist&wd={urllib.parse.quote(wd)}&pg={pg}"
    else:
        url = f"{api_url}?ac=videolist&t={cid}&pg={pg}"

    data = get_json(url)
    videos = data.get("list", [])

    for v in videos:
        title = v.get("vod_name")
        play_url = v.get("vod_play_url", "")
        li = xbmcgui.ListItem(label=title)
        li.setInfo("video", {"title": title})
        if play_url:
            first_play = play_url.split("#")[0]
            link = first_play.split("$")[-1] if "$" in first_play else first_play
            xbmcplugin.addDirectoryItem(addon_handle, link, li, isFolder=False)

    # 下一页
    if videos:
        next_pg = int(pg) + 1
        li = xbmcgui.ListItem(label="下一页 >>")
        url = build_url({"mode": "list_videos", "api": api_url, "cid": cid, "pg": next_pg, "wd": wd or ""})
        xbmcplugin.addDirectoryItem(addon_handle, url, li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)


# ========== 搜索 ==========
def search_videos(api_url):
    kb = xbmc.Keyboard("", "输入关键词")
    kb.doModal()
    if kb.isConfirmed():
        wd = kb.getText()
        if wd:
            list_videos(api_url, cid="", pg=1, wd=wd)
        else:
            xbmcgui.Dialog().notification("提示", "未输入关键词", xbmcgui.NOTIFICATION_INFO)
    else:
        xbmcplugin.endOfDirectory(addon_handle)


# ========== 路由 ==========
mode = args.get("mode", [None])[0]

if mode is None:
    list_sources()
elif mode == "list_categories":
    api = args.get("api", [""])[0]
    list_categories(api)
elif mode == "list_videos":
    api = args.get("api", [""])[0]
    cid = args.get("cid", [""])[0]
    pg = args.get("pg", ["1"])[0]
    wd = args.get("wd", [""])[0] or None
    list_videos(api, cid, pg, wd)
elif mode == "search":
    api = args.get("api", [""])[0]
    search_videos(api)
