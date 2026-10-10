import urllib.error
from datetime import datetime, timezone

import check
from check import parse_feed

FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
 <title>Uploads from 채널</title>
 <author><name>채널</name></author>
 <entry><yt:videoId>new</yt:videoId><title>최신</title><published>2026-10-05T05:45:54+00:00</published></entry>
 <entry><yt:videoId>old</yt:videoId><title>예전</title><published>2026-10-01T00:00:00+00:00</published></entry>
</feed>"""

author, entries = parse_feed(FEED)
assert author == "채널" and [(v, t) for v, t, _ in entries] == [("old", "예전"), ("new", "최신")]
assert entries[1][2] == datetime(2026, 10, 5, 5, 45, 54, tzinfo=timezone.utc)

# 피드가 계속 404여도 두 주소를 번갈아 재시도해 성공해야 하고, POST는 재시도하지 않아야 한다
calls = []


class Ok:
    def __enter__(self): return self
    def __exit__(self, *a): pass
    def read(self): return FEED.encode()


def flaky(req, timeout):
    calls.append(req.full_url)
    if len(calls) < 3:
        raise urllib.error.HTTPError(req.full_url, 404, "Not Found", None, None)
    return Ok()


check.urllib.request.urlopen = flaky
check.time.sleep = lambda s: None
assert check.fetch_feed("UCabc")[0] == "채널" and len(calls) == 3
assert "playlist_id=UUabc" in calls[0] and "channel_id=UCabc" in calls[1]
calls.clear()
try:
    check.fetch("http://x", {"content": "hi"})
    raise SystemExit("POST가 재시도됨")
except urllib.error.HTTPError:
    assert len(calls) == 1
print("ok")
