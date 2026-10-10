"""YouTube 채널 RSS 피드를 확인해 새 영상/방송을 Discord 웹후크로 알린다."""
import json
import os
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET

# 채널 ID: 웹후크 URL이 담긴 환경변수(GitHub Secret) 이름
CHANNELS = {
    "UCJMW5nKtT9uSHWINC-aAUPw": "WEBHOOK_TIPP7",  # 팁7 (@GMDTipp7)
    "UCEnjAAmVQ9wx8CDPDV6Y4sg": "WEBHOOK_JYOBU",  # 죠브
}
SEEN_FILE = "seen.json"
FEED = "https://www.youtube.com/feeds/videos.xml?channel_id="
WATCH = "https://www.youtube.com/watch?v="
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}


def fetch(url, payload=None):
    # Discord는 urllib 기본 User-Agent를 403으로 막는다
    headers = {"User-Agent": "Mozilla/5.0 (yt-notify)", "Accept-Language": "ko"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    # YouTube 피드는 간헐적으로 404/500을 낸다 -> GET만 재시도 (POST 재시도는 중복 알림 위험)
    waits = [3, 6, 12] if payload is None else []
    while True:
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read().decode("utf-8", "replace")
        except OSError:  # HTTPError, URLError, 타임아웃 모두 포함
            if not waits:
                raise
            time.sleep(waits.pop(0))


def parse_feed(xml):
    """피드 XML -> (채널명, [(video_id, 제목)]) — 오래된 것부터."""
    root = ET.fromstring(xml)
    entries = [
        (e.findtext("yt:videoId", "", NS), e.findtext("a:title", "", NS))
        for e in root.findall("a:entry", NS)
    ]
    return root.findtext("a:title", "", NS), entries[::-1]


def label(video_id):
    # shortcut: 피드에는 방송 여부가 없어 영상 페이지 문자열로 추정한다. 페이지가 막히면
    # 그냥 "새 영상"으로 나간다. 정확해야 하면 YouTube Data API(키 필요)로 바꿀 것.
    try:
        page = fetch(WATCH + video_id)
    except Exception:
        page = ""
    if '"isLiveNow":true' in page:
        return "🔴 방송 시작"
    if '"isUpcoming":true' in page:
        return "⏰ 방송 예정"
    return "🎬 새 영상"


def main():
    seen = {}
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            seen = json.load(f)
    failed = False
    for cid, env in CHANNELS.items():
        try:
            author, entries = parse_feed(fetch(FEED + cid))
            if cid not in seen:
                # 첫 실행: 과거 영상은 건너뛰고 최신 1개만 알려서 동작을 확인한다
                seen[cid] = [vid for vid, _ in entries[:-1]]
            for vid, title in entries:
                if vid in seen[cid]:
                    continue
                fetch(os.environ[env], {
                    "content": f"{label(vid)} | **{author}**\n{title}\n{WATCH}{vid}",
                    "allowed_mentions": {"parse": []},  # 제목에 @everyone이 있어도 멘션 안 됨
                })
                seen[cid].append(vid)  # 전송 성공한 것만 기록 -> 실패하면 다음 실행에서 재시도
        except Exception as e:
            print(f"{cid}: {type(e).__name__}: {e}", file=sys.stderr)
            failed = True
    with open(SEEN_FILE, "w") as f:
        json.dump(seen, f, indent=1)
    sys.exit(failed)


if __name__ == "__main__":
    main()
