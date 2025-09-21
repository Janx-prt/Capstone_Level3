import os
import requests


def post_to_x(article):
    token = os.getenv('X_BEARER_TOKEN')
    if not token:
        return
    # Compose tweet text (keep under 280 chars)
    base = f"{article.title} — by {article.author.username} via {article.publisher.name}"
    # placeholder; align to your account/app settings
    url = "https://api.x.com/2/tweets"
    payload = {"text": base[:260]}
    headers = {"Authorization": f"Bearer {token}",
               "Content-Type": "application/json"}
    try:
        requests.post(url, json=payload, headers=headers, timeout=10)
    except requests.RequestException:
        pass
