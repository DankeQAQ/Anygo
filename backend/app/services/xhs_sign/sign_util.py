"""
小红书请求签名工具
基于 Spider_XHS 项目的 JS 签名引擎，通过 PyExecJS 调用本地 Node.js 执行签名 JS
生成 x-s, x-t, x-s-common, x-b3-traceid, x-xray-traceid 等请求头字段
"""

import json
import math
import random
import os
import execjs
from execjs._misc import encode_unicode_codepoints
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'zh_CN.UTF-8'

# ---------- JS 运行时初始化 ----------
_SIGN_DIR = os.path.dirname(os.path.abspath(__file__))


def _compile_js(js_code: str):
    """
    将 JS 源码中的非 ASCII 字符转义为 \\uXXXX，避免 Windows 上 stdin 管道
    按系统代码页（例如 cp932）写入时触发 UnicodeEncodeError。
    """
    return execjs.compile(encode_unicode_codepoints(js_code))

# 加载核心签名 JS（生成 x-s / x-t / x-s-common）
_xs_js_path = os.path.join(_SIGN_DIR, "xhs_xs_xsc_56.js")
with open(_xs_js_path, "r", encoding="utf-8") as f:
    _xs_js = _compile_js(f.read())

# 加载 xray traceid JS
_xray_js_path = os.path.join(_SIGN_DIR, "xhs_xray.js")
with open(_xray_js_path, "r", encoding="utf-8") as f:
    _xray_js_code = f.read()

# 动态替换JS中的相对路径require为绝对路径，防止execjs从stdin执行时找不到包
import re
_pack1_path = os.path.join(_SIGN_DIR, "xhs_xray_pack1.js").replace('\\', '/')
_pack2_path = os.path.join(_SIGN_DIR, "xhs_xray_pack2.js").replace('\\', '/')
_xray_js_code = re.sub(r"require\(['\"].*?xhs_xray_pack[12]\.js['\"]\)", 
                       lambda m: f"require('{_pack1_path}')" if "pack1" in m.group(0) else f"require('{_pack2_path}')", 
                       _xray_js_code)

_xray_js = _compile_js(_xray_js_code)

print("[XHS_SIGN] signature JS engine loaded")


# ---------- Cookie 工具 ----------
def trans_cookies(cookies_str: str) -> dict:
    """将 Cookie 字符串转为字典"""
    sep = "; " if "; " in cookies_str else ";"
    ck = {}
    for item in cookies_str.split(sep):
        parts = item.split("=", 1)
        if len(parts) == 2:
            ck[parts[0].strip()] = parts[1].strip()
    return ck


# ---------- 签名生成 ----------
def generate_x_b3_traceid(length: int = 16) -> str:
    """生成 x-b3-traceid"""
    chars = "abcdef0123456789"
    return "".join(chars[math.floor(16 * random.random())] for _ in range(length))


def generate_xray_traceid() -> str:
    """生成 x-xray-traceid"""
    return _xray_js.call("traceId")


def generate_xs_xs_common(a1: str, api: str, data="", method="POST"):
    """调用签名 JS 生成 x-s, x-t, x-s-common"""
    ret = _xs_js.call("get_request_headers_params", api, data, a1, method)
    return ret["xs"], ret["xt"], ret["xs_common"]


def _get_request_headers_template() -> dict:
    """构建基础请求头模板"""
    return {
        "authority": "edith.xiaohongshu.com",
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "cache-control": "no-cache",
        "content-type": "application/json;charset=UTF-8",
        "origin": "https://www.xiaohongshu.com",
        "pragma": "no-cache",
        "referer": "https://www.xiaohongshu.com/",
        "sec-ch-ua": '"Not A(Brand";v="99", "Microsoft Edge";v="121", "Chromium";v="121"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
        "x-b3-traceid": "",
        "x-mns": "unload",
        "x-s": "",
        "x-s-common": "",
        "x-t": "",
        "x-xray-traceid": generate_xray_traceid(),
    }


def generate_headers(a1: str, api: str, data="", method="POST"):
    """生成带完整签名的请求头，返回 (headers, serialized_data)"""
    xs, xt, xs_common = generate_xs_xs_common(a1, api, data, method)
    headers = _get_request_headers_template()
    headers["x-s"] = xs
    headers["x-t"] = str(xt)
    headers["x-s-common"] = xs_common
    headers["x-b3-traceid"] = generate_x_b3_traceid()

    if data:
        data = json.dumps(data, separators=(",", ":"), ensure_ascii=False)

    return headers, data


def generate_request_params(cookies_str: str, api: str, data="", method="POST"):
    """
    一站式生成带签名的请求参数

    Args:
        cookies_str: Cookie 字符串
        api: API 路径 (如 /api/sns/web/v1/search/notes)
        data: 请求体 (dict 或空字符串)
        method: HTTP 方法

    Returns:
        (headers, cookies_dict, serialized_data)
    """
    cookies = trans_cookies(cookies_str)
    a1 = cookies.get("a1", "")
    headers, data = generate_headers(a1, api, data, method)
    return headers, cookies, data


def splice_str(api: str, params: dict) -> str:
    """将 API 路径与查询参数拼接"""
    url = api + "?"
    for key, value in params.items():
        if value is None:
            value = ""
        url += key + "=" + str(value) + "&"
    return url[:-1]
