import json
import urllib.error

import check

FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
 <title>채널</title>
 <entry><yt:videoId>new</yt:videoId><title>최신</title></entry>
 <entry><yt:videoId>old</yt:videoId><title>예전</title></entry>
</feed>"""


def item(vid, title):
    return {"lockupViewModel": {
        "contentId": vid,
        "contentType": "LOCKUP_CONTENT_TYPE_VIDEO",
        "metadata": {"lockupMetadataViewModel": {"title": {"content": title}}},
    }}


PAGE = "<script>var ytInitialData = %s;</script>" % json.dumps(
    {"contents": {"x": [{"y": [item("new", "최신"), item("old", "예전"), {"continuationItemViewModel": {}}]}]}}
)
VIDEOS = [("new", "최신"), ("old", "예전")]

assert check.parse_feed(FEED) == VIDEOS
assert check.parse_playlist(PAGE) == VIDEOS

# 새 영상: 이미 알린 영상 위쪽만, 오래된 것부터, 최대 5개
assert check.new_videos(VIDEOS, ["old"]) == [("new", "최신")]
assert check.new_videos(VIDEOS, ["new"]) == []  # 알린 영상 아래의 옛 영상은 무시
assert check.new_videos([(str(i), "") for i in range(9)], []) == [(str(i), "") for i in (4, 3, 2, 1, 0)]

# 재생목록 페이지가 깨지면 피드로 넘어가고, 피드는 404가 나도 재시도한다
calls = []


def fake_fetch(url, payload=None):
    calls.append(url)
    if "playlist" in url:
        return "<html>구조가 바뀜</html>"
    if len(calls) < 4:
        raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
    return FEED


check.fetch = fake_fetch
check.time.sleep = lambda s: None
assert check.latest("UCabc") == VIDEOS
assert calls[0].endswith("list=UUabc") and calls[1:] == [check.FEED + "UCabc"] * 3
print("ok")
