"""YouTube 채널의 새 영상/방송을 Discord 웹후크로 알린다."""
import json
import os
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET

# 채널 ID: (알림에 표시할 이름, 웹후크 URL이 담긴 환경변수(GitHub Secret) 이름)
CHANNELS = {
    "UCJMW5nKtT9uSHWINC-aAUPw": ("Geometry dash Tipp7", "WEBHOOK_TIPP7"),  # @GMDTipp7
    "UCEnjAAmVQ9wx8CDPDV6Y4sg": ("죠브", "WEBHOOK_JYOBU"),
}
SEEN_FILE = "seen.json"
PLAYLIST = "https://www.youtube.com/playlist?list=UU"  # 업로드 재생목록: 채널 ID의 UC -> UU
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
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", "replace")


def parse_playlist(html):
    """업로드 재생목록 페이지 -> [(video_id, 제목)] — 최신 것부터."""
    m = re.search(r"var ytInitialData = (\{.*?\});</script>", html, re.S)
    if not m:
        raise ValueError("ytInitialData 없음")
    videos = []

    def walk(o):
        if isinstance(o, dict):
            if o.get("contentType") == "LOCKUP_CONTENT_TYPE_VIDEO":
                title = o["metadata"]["lockupMetadataViewModel"]["title"]["content"]
                videos.append((o["contentId"], title))
            else:
                for v in o.values():
                    walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(json.loads(m.group(1)))
    if not videos:
        raise ValueError("재생목록에서 영상을 찾지 못함")
    return videos


def parse_feed(xml):
    """RSS 피드 XML -> [(video_id, 제목)] — 최신 것부터."""
    return [
        (e.findtext("yt:videoId", "", NS), e.findtext("a:title", "", NS))
        for e in ET.fromstring(xml).findall("a:entry", NS)
    ]


def latest(cid):
    """채널의 최근 영상 [(video_id, 제목)] — 최신 것부터."""
    # RSS 피드는 GitHub 러너에서 몇 분씩 통째로 404/500이 난다 (2026-10-10 실측: 러너 6대 중
    # 2대가 4분 내내 실패). 재생목록 페이지는 같은 실측에서 24/24 성공해서 이쪽을 먼저 쓰고,
    # 페이지 구조가 바뀌어 못 읽을 때만 피드로 넘어간다.
    try:
        return parse_playlist(fetch(PLAYLIST + cid[2:]))
    except (OSError, ValueError, LookupError) as e:
        print(f"::warning::{cid}: 재생목록 페이지 실패 ({type(e).__name__}: {e}) -> 피드 사용")
    for left in reversed(range(10)):
        try:
            return parse_feed(fetch(FEED + cid))
        except (OSError, ET.ParseError):
            if not left:
                raise
            time.sleep(6)


def new_videos(videos, seen_ids):
    """아직 알리지 않은 새 영상 — 오래된 것부터."""
    new = []
    for video in videos:
        # 이미 알린 영상이 나오면 멈춘다. 그 아래의 모르는 영상은 최근 영상이 삭제되어
        # 목록에 다시 올라온 옛 영상이다.
        if video[0] in seen_ids:
            break
        new.append(video)
    # shortcut: 한 번에 최신 5개까지만 알린다(오작동 시 도배 방지). 실행 간격 사이에
    # 한 채널에 6개 이상 올라오면 오래된 것은 빠진다.
    return new[:5][::-1]


def label(video_id):
    # shortcut: 목록에는 방송 여부가 없어 영상 페이지 문자열로 추정한다. 페이지가 막히면
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
    for cid, (name, env) in CHANNELS.items():
        try:
            videos = latest(cid)
            if cid not in seen:
                # 첫 실행: 과거 영상은 건너뛰고 최신 1개만 알려서 동작을 확인한다
                seen[cid] = [vid for vid, _ in videos[1:]]
            for vid, title in new_videos(videos, seen[cid]):
                fetch(os.environ[env], {
                    "content": f"{label(vid)} | **{name}**\n{title}\n{WATCH}{vid}",
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
