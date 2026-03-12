import re
from urllib.parse import parse_qs, urlparse

from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def multiply(value, arg):
    return value * arg


def _youtube_id(parsed):
    if parsed.hostname in ('www.youtube.com', 'youtube.com'):
        qs = parse_qs(parsed.query)
        vid = qs.get('v', [None])[0]
        if vid:
            return vid
        # Shorts: /shorts/ID
        match = re.match(r'^/shorts/([^/?]+)', parsed.path)
        if match:
            return match.group(1)
    if parsed.hostname == 'youtu.be':
        return parsed.path.lstrip('/').split('?')[0] or None
    return None


@register.filter
def video_thumbnail_url(url):
    if not url:
        return None
    vid = _youtube_id(urlparse(url))
    return f'https://img.youtube.com/vi/{vid}/hqdefault.jpg' if vid else None
