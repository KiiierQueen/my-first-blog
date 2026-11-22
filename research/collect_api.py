"""Сбор данных YouTube Data API по рынкам. Ключ читается из файла (путь в YT_KEY_FILE), в репозиторий не попадает."""
import os, json, csv, re, sys, datetime as dt, urllib.request, urllib.parse

KEY = open(os.environ["YT_KEY_FILE"]).read().strip()
# рынок -> (regionCode, язык, запросы)
MARKETS = {
    "US": ("US", "en", ["AI generated story", "AI tools tutorial", "AI video"]),
    "BR": ("BR", "pt", ["história feita com IA", "ferramentas de inteligência artificial", "vídeo com IA"]),
    "DE": ("DE", "de", ["KI Geschichte", "KI Tools Tutorial", "KI Video"]),
    "MX": ("MX", "es", ["historia hecha con IA", "herramientas de inteligencia artificial", "video con IA"]),
    "TR": ("TR", "tr", ["yapay zeka hikaye", "yapay zeka araçları", "yapay zeka video"]),
    "PL": ("PL", "pl", ["historia AI", "narzędzia sztucznej inteligencji", "film AI"]),
    "ID": ("ID", "id", ["cerita buatan AI", "tools kecerdasan buatan", "video AI"]),
    "CA": ("CA", "en", ["AI generated story", "AI tools tutorial", "AI video"]),
    "GB": ("GB", "en", ["AI generated story", "AI tools tutorial", "AI video"]),
    "NL": ("NL", "nl", ["AI verhaal", "AI tools tutorial", "AI video"]),
    "SE": ("SE", "sv", ["AI berättelse", "AI verktyg tutorial", "AI video"]),
    "CZ": ("CZ", "cs", ["AI příběh", "AI nástroje návod", "AI video"]),
}
if os.environ.get("ONLY"): MARKETS = {k: v for k, v in MARKETS.items() if k in os.environ["ONLY"].split(",")}
def api(path, **p):
    p["key"] = KEY
    with urllib.request.urlopen(f"https://www.googleapis.com/youtube/v3/{path}?" + urllib.parse.urlencode(p), timeout=60) as r:
        return json.load(r)
def dur(s):
    m = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s or "")
    h, mi, se = (int(x or 0) for x in m.groups()) if m else (0, 0, 0)
    return h*3600 + mi*60 + se

after = (dt.datetime.utcnow() - dt.timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
rows = []
for mk, (region, lang, queries) in MARKETS.items():
    ids = {}
    for q in queries:
        r = api("search", part="snippet", q=q, type="video", regionCode=region, relevanceLanguage=lang,
                publishedAfter=after, order="viewCount", maxResults=50)
        for it in r.get("items", []):
            ids[it["id"]["videoId"]] = q
    vids = []
    idl = list(ids)
    for i in range(0, len(idl), 50):
        vids += api("videos", part="snippet,statistics,contentDetails", id=",".join(idl[i:i+50]))["items"]
    chans = {}
    cl = list({v["snippet"]["channelId"] for v in vids})
    for i in range(0, len(cl), 50):
        for c in api("channels", part="statistics,snippet", id=",".join(cl[i:i+50]))["items"]:
            chans[c["id"]] = (int(c["statistics"].get("subscriberCount", 0)), c["snippet"].get("country"))
    for v in vids:
        d = dur(v["contentDetails"]["duration"]); st = v["statistics"]
        subs, ctry = chans.get(v["snippet"]["channelId"], (0, None))
        rows.append(dict(market=mk, query=ids[v["id"]], id=v["id"], title=v["snippet"]["title"],
            channel=v["snippet"]["channelTitle"], channel_id=v["snippet"]["channelId"], channel_country=ctry,
            subs=subs, views=int(st.get("viewCount", 0)), likes=int(st.get("likeCount", 0)),
            duration=d, is_short=d <= 60, published=v["snippet"]["publishedAt"][:10]))
    print(mk, len(vids), flush=True)
with open(os.environ.get("OUT","videos.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print("saved", len(rows))
