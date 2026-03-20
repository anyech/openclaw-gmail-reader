#!/usr/bin/env python3
"""Shared markdown-safety helpers for generated Gmail preview text.

Preview/snippet text is treated as plain content, not intentional Markdown.
That means we prefer safe escaping of markdown-significant punctuation over
trying to preserve fancy inline formatting from arbitrary emails.
"""

from __future__ import annotations

import re

_INLINE_MARKERS_RE = re.compile(r'(?<!\\)([\*\[\]])')
_UNESCAPED_UNDERSCORE_RE = re.compile(r'(?<!\\)_')
_WHITESPACE_RE = re.compile(r'\s+')


def sanitize_markdown_preview(text: str) -> str:
    """Normalize preview text so generated Markdown stays lint-safe.

    Rules:
    - collapse newlines / repeated whitespace into a single space
    - preserve text content, but escape markdown-significant inline markers
    - stay idempotent so repeated fixer runs are harmless
    """
    if not text:
        return ''

    text = text.replace('\r', ' ').replace('\n', ' ')
    text = _WHITESPACE_RE.sub(' ', text).strip()
    text = _UNESCAPED_UNDERSCORE_RE.sub(r'\\_', text)
    text = _INLINE_MARKERS_RE.sub(r'\\\1', text)
    return text
