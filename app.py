import feedparser
import requests
import time
import json
import re
import os

PAGE_TOKEN = os.getenv("PAGE_TOKEN")

feeds = [
    ("GMA News", "https://www.gmanetwork.com/news/rss/"),
    ("TV5 News", "https://interaksyon.philstarht.com/feed/"),
    ("ABS-CBN News", "https://news.abs-cbn.com/rss")
]

# load saved topics
try:
    with open("topics.json", "r") as f:
        used_topics = set(json.load(f))
except:
    used_topics = set()

def save_topics():
    with open("topics.json", "w") as f:
        json.dump(list(used_topics), f)

# normalize text
def normalize(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9 ]', '', text)
    return text

# extract keywords
def extract_keywords(title):
    words = normalize(title).split()
    blacklist = ["the", "a", "an", "ng", "sa", "ang", "and", "to", "of"]

    keywords = [w for w in words if w not in blacklist and len(w) > 3]
    return " ".join(keywords[:4])

# check duplicate
def is_duplicate(topic):
    for old in used_topics:
        if topic in old or old in topic:
            return True
    return False

# breaking detection
important_keywords = [
    "bagyo", "storm", "lindol", "earthquake",
    "sunog", "fire", "accident", "crash",
    "patay", "killed", "alert", "warning",
    "president", "law", "increase", "emergency"
]

def is_breaking(title):
    title = title.lower()
    return any(word in title for word in important_keywords)

# emoji detection
def get_emoji(title):
    title = title.lower()

    if "bagyo" in title or "storm" in title or "ulan" in title:
        return "🌧️"
    elif "lindol" in title or "earthquake" in title:
        return "🌍"
    elif "sunog" in title or "fire" in title:
        return "🔥"
    elif "accident" in title or "crash" in title or "bangga" in title:
        return "🚗"
    elif "president" in title or "batas" in title or "government" in title:
        return "🏛️"
    elif "celebrity" in title or "artista" in title:
        return "🎤"
    else:
        return "📰"

# get image
def get_image(entry):
    if "media_content" in entry:
        return entry.media_content[0]['url']
    if "media_thumbnail" in entry:
        return entry.media_thumbnail[0]['url']
    if "links" in entry:
        for link in entry.links:
            if "image" in link.type:
                return link.href
    return None

def post_news():
    for source_name, url in feeds:
        feed = feedparser.parse(url)

        for entry in feed.entries[:1]:
            topic = extract_keywords(entry.title)

            if not is_duplicate(topic):

                emoji = get_emoji(entry.title)
                image_url = get_image(entry)

                if is_breaking(entry.title):
                    header = "🚨 BREAKING NEWS\n\n"
                    hashtags = "#Balita #ViralScoopPH #BreakingNews"
                else:
                    header = ""
                    hashtags = "#Balita #ViralScoopPH"

                message = f"""{header}{emoji} {entry.title}

📌 Source: {source_name}
🔗 {entry.link}

{hashtags}"""

                if image_url:
                    requests.post(
                        "https://graph.facebook.com/v18.0/me/photos",
                        data={
                            "url": image_url,
                            "caption": message,
                            "access_token": PAGE_TOKEN
                        }
                    )
                else:
                    requests.post(
                        "https://graph.facebook.com/v18.0/me/feed",
                        data={
                            "message": message,
                            "access_token": PAGE_TOKEN
                        }
                    )

                used_topics.add(topic)
                save_topics()
                time.sleep(20)

while True:
    post_news()
    time.sleep(300)