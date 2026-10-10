import urllib.error

import check
from check import parse_feed

FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
 <title>채널</title>
 <entry><yt:videoId>new</yt:videoId><title>최신</title></entry>
 <entry><yt:videoId>old</yt:videoId><title>예전</title></entry>
</feed>"""

assert parse_feed(FEED) == ("채널", [("old", "예전"), ("new", "최신")])

# 피드가 일시적으로 404를 내도 재시도해서 성공해야 하고, POST는 재시도하지 않아야 한다
calls = []


class Ok:
    def __enter__(self): return self
    def __exit__(self, *a): pass
    def read(self): return b"body"


def flaky(req, timeout):
    calls.append(req)
    if len(calls) < 3:
        raise urllib.error.HTTPError(req.full_url, 404, "Not Found", None, None)
    return Ok()


check.urllib.request.urlopen = flaky
check.time.sleep = lambda s: None
assert check.fetch("http://x") == "body" and len(calls) == 3
calls.clear()
try:
    check.fetch("http://x", {"content": "hi"})
    raise SystemExit("POST가 재시도됨")
except urllib.error.HTTPError:
    assert len(calls) == 1
print("ok")
