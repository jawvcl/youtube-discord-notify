from check import parse_feed

FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
 <title>채널</title>
 <entry><yt:videoId>new</yt:videoId><title>최신</title></entry>
 <entry><yt:videoId>old</yt:videoId><title>예전</title></entry>
</feed>"""

assert parse_feed(FEED) == ("채널", [("old", "예전"), ("new", "최신")])
print("ok")
