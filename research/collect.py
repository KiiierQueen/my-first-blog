"""Сбор метаданных YouTube по рынкам (язык/страна) через yt-dlp. Видео не скачиваются."""
import json, subprocess, sys, csv, datetime as dt

# рынок -> (код страны, запросы на местном языке про ИИ-контент)
MARKETS = {
    "US": ("US", ["AI generated story", "AI tools tutorial", "AI video"]),
    "BR": ("BR", ["história feita com IA", "ferramentas de inteligência artificial", "vídeo com IA"]),
    "DE": ("DE", ["KI Geschichte", "KI Tools Tutorial", "KI Video"]),
    "ES-MX": ("MX", ["historia hecha con IA", "herramientas de inteligencia artificial", "video con IA"]),
    "TR": ("TR", ["yapay zeka hikaye", "yapay zeka araçları", "yapay zeka video"]),
    "PL": ("PL", ["historia AI", "narzędzia sztucznej inteligencji", "film AI"]),
    "ID": ("ID", ["cerita buatan AI", "tools kecerdasan buatan", "video AI"]),
}
PER_QUERY = int(sys.argv[1]) if len(sys.argv) > 1 else 10

def fetch(query, country, n):
    cmd = ["yt-dlp", "--skip-download", "--dump-json", "--no-warnings", "--ignore-errors",
           "--geo-bypass-country", country, f"ytsearch{n}:{query}", "--dateafter", "today-60days"]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=600).stdout
    return [json.loads(l) for l in out.splitlines() if l.startswith("{")]

rows = []
for market, (cc, queries) in MARKETS.items():
    for q in queries:
        for v in fetch(q, cc, PER_QUERY):
            rows.append(dict(market=market, query=q, id=v.get("id"), title=v.get("title"),
                channel=v.get("channel"), subs=v.get("channel_follower_count"),
                views=v.get("view_count"), likes=v.get("like_count"),
                duration=v.get("duration"), upload_date=v.get("upload_date"),
                is_short=bool(v.get("duration") and v["duration"] <= 60)))
        print(market, q, len(rows), flush=True)

with open("videos.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
print("saved", len(rows))
