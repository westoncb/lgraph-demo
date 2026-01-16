from __future__ import annotations

from typing import Tuple

import trafilatura


def extract_article_text(url: str, word_limit: int = 1000) -> Tuple[str, int, str | None]:
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        return "", 0, "failed to download article"

    text = trafilatura.extract(downloaded)
    if not text:
        return "", 0, "failed to extract text"

    words = text.split()
    truncated_words = words[:word_limit]
    truncated_text = " ".join(truncated_words)
    return truncated_text, len(truncated_words), None
