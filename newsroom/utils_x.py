"""
Integration with X (formerly Twitter) for posting articles.

This module provides a helper function to publish article updates
to X using its API.
"""

import os
import requests


def post_to_x(article):
    """
    Post an article announcement to X (Twitter).

    This function composes a short message including the article
    title, author username, and publisher name, and posts it to
    X using the v2 API.

    Parameters
    ----------
    article : Article
        An article instance with attributes:
        - ``title`` (str): Title of the article.
        - ``author.username`` (str): Username of the article's author.
        - ``publisher.name`` (str): Name of the publisher.

    Notes
    -----
    - Requires the environment variable ``X_BEARER_TOKEN`` to be set
      with a valid API bearer token.
    - The composed text is truncated to 260 characters to stay under
      the 280-character limit.
    - The request is sent to ``https://api.x.com/2/tweets``.
    - Any exceptions from :mod:`requests` are suppressed silently.
    """
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
