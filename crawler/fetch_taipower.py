import os
import json
import ssl
import hashlib
from datetime import datetime, timezone, timedelta

import requests
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # repo root
DATA_DIR = ROOT / "data" / "crawler"

WEEKLY_DIR = DATA_DIR / "weekly"
ANNUAL_DIR = DATA_DIR / "annual"

WEEKLY_DIR.mkdir(parents=True, exist_ok=True)
ANNUAL_DIR.mkdir(parents=True, exist_ok=True)

# 台灣時區
TZ_TW = timezone(timedelta(hours=8))

APIS = {
    "d006010_001": "https://service.taipower.com.tw/data/opendata/apply/file/d006010/001.json",
    "d006009_001": "https://service.taipower.com.tw/data/opendata/apply/file/d006009/001.json",
}


OUT_WEEKLY_DIR = WEEKLY_DIR / api_key / f"{ymd}.json"
OUT_ANNUAL_DIR = ANNUAL_DIR / api_key / f"{year}.jsonl"


def ensure_dirs():
    os.makedirs(OUT_WEEKLY_DIR, exist_ok=True)
    os.makedirs(OUT_ANNUAL_DIR, exist_ok=True)


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def write_text(path: str, text: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def safe_get(url: str) -> str:
    # 你原本用 verify=False；Actions 環境通常不需要關掉 SSL 驗證
    # 如果你一定要保留 verify=False，可以改成 requests.get(url, verify=False, timeout=60)
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.text


def update_annual_jsonl(api_key: str, fetched_at: str, payload_text: str):
    """
    年度累積：建議用 JSONL（每行一筆），避免每週把巨大 JSON 合併到同一個 dict 很痛苦。
    annual/<api_key>/<year>.jsonl
    每行格式：{"fetched_at": "...", "sha256": "...", "payload": <原始JSON解析後物件>}
    """
    year = datetime.now(TZ_TW).year
    out_dir = os.path.join(OUT_ANNUAL_DIR, api_key)
    os.makedirs(out_dir, exist_ok=True)

    out_path = os.path.join(out_dir, f"{year}.jsonl")

    payload_obj = None
    try:
        payload_obj = json.loads(payload_text)
    except json.JSONDecodeError:
        # 如果 API 回來不是標準 JSON（極少見），就把原文存起來
        payload_obj = {"_raw": payload_text}

    record = {
        "fetched_at": fetched_at,
        "sha256": sha256_text(payload_text),
        "payload": payload_obj,
    }

    with open(out_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main():
    ensure_dirs()

    now = datetime.now(TZ_TW)
    fetched_at = now.isoformat(timespec="seconds")
    ymd = now.strftime("%Y%m%d")

    changed_any = False

    for api_key, url in APIS.items():
        print(f"[INFO] Fetching {api_key} from {url}")
        text = safe_get(url)

        # 週檔：weekly/<api_key>/<YYYYMMDD>.json
        api_weekly_dir = os.path.join(OUT_WEEKLY_DIR, api_key)
        os.makedirs(api_weekly_dir, exist_ok=True)
        weekly_path = os.path.join(api_weekly_dir, f"{ymd}.json")
        write_text(weekly_path, text)
        print(f"[OK] Wrote weekly: {weekly_path}")

        # 如果本週抓到的內容跟上次一樣，也照樣留週檔，但年度累積避免重複寫入（可選）
        # 用 last snapshot hash 判斷
        last_hash_path = os.path.join(api_weekly_dir, "_last_sha256.txt")
        new_hash = sha256_text(text)

        old_hash = None
        if os.path.exists(last_hash_path):
            old_hash = read_text(last_hash_path).strip()

        if old_hash != new_hash:
            # 年度累積更新（只在內容變了才追加一筆，避免年度檔爆長）
            update_annual_jsonl(api_key, fetched_at, text)
            write_text(last_hash_path, new_hash)
            print(f"[OK] Annual updated for {api_key}")
            changed_any = True
        else:
            print(f"[SKIP] Content unchanged for {api_key}; annual not appended.")

    # 提供給 GitHub Action 判斷要不要 commit
    # 你也可以只要 weekly 有新檔就 commit（那就改成永遠 True）
    with open("changed.flag", "w", encoding="utf-8") as f:
        f.write("1" if changed_any else "0")

    print("[DONE]")


if __name__ == "__main__":
    main()
