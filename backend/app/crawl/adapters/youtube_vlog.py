"""Korean vlog captions as topic-segment documents; media is never downloaded."""
import importlib
import json

from app.config import settings
from app.crawl.adapters.base import AdapterBlocked, AdapterSkipped, FetchedDoc, ListItem, ListPage
from app.crawl.adapters.youtube import YoutubeAdapter, _blocked, _date, _metadata, extract_info
from app.crawl.captions import parse_json3, segment

_UNSET = object()


def _korean_track(info):
    for kind, key, langs in (('manual', 'subtitles', ('ko',)), ('auto', 'automatic_captions', ('ko-orig', 'ko'))):
        tracks = info.get(key) or {}
        for lang in langs:
            for track in tracks.get(lang) or []:
                if track.get('ext') == 'json3' and track.get('url'):
                    return track, kind
    return None, None


class YoutubeVlogAdapter:
    source = 'youtube_vlog'

    @classmethod
    def is_available(cls) -> bool:
        return YoutubeAdapter.is_available()

    def __init__(self, embedder_factory=None):
        if embedder_factory is None:
            from app.vectors.embedder import get_embedder
            embedder_factory = get_embedder
        self._factory = embedder_factory
        self._embedder = _UNSET

    def _get_embedder(self):
        if self._embedder is _UNSET:
            try:
                self._embedder = self._factory()
            except Exception:
                self._embedder = None
        return self._embedder

    def list_page(self, kw, cursor, *, videos_per_keyword=20, min_duration_s=60, max_duration_s=3600):
        if cursor is not None:
            raise ValueError('YouTube search has no continuation cursor')
        if videos_per_keyword <= 0:
            raise ValueError('videos_per_keyword must be positive')
        info = extract_info(f'ytsearch{videos_per_keyword * 2}:{kw} 브이로그', extract_flat=True)
        items = []
        for entry in info.get('entries') or []:
            duration = (entry or {}).get('duration')
            if not entry or not entry.get('id') or duration is None:
                continue
            if not min_duration_s <= duration <= max_duration_s:
                continue
            items.append(ListItem(f"https://www.youtube.com/watch?v={entry['id']}", entry.get('title') or '',
                                  entry.get('description') or '', _date(entry), _metadata(entry)))
            if len(items) >= videos_per_keyword:
                break
        return ListPage(items, None, len(items))

    def fetch(self, item):
        yt_dlp = importlib.import_module('yt_dlp')
        try:
            with yt_dlp.YoutubeDL(dict(quiet=True, no_warnings=True, skip_download=True)) as ydl:
                info = ydl.extract_info(item.url, download=False)
                track, kind = _korean_track(info or {})
                if track is None:
                    raise AdapterSkipped('no_ko_captions')
                data = json.loads(ydl.urlopen(track['url']).read().decode('utf-8'))
        except (AdapterSkipped, AdapterBlocked):
            raise
        except Exception as exc:
            if _blocked(exc):
                raise AdapterBlocked('YouTube blocked the request') from exc
            raise
        cues = parse_json3(data)
        if not cues:
            raise AdapterSkipped('no_ko_captions')
        segments, method = segment(cues, self._get_embedder(), window_s=settings.caption_window_s,
                                   min_s=settings.caption_min_segment_s, max_s=settings.caption_max_segment_s,
                                   fixed_s=settings.caption_fixed_segment_s)
        meta = _metadata(info)
        author = info.get('channel_id') or info.get('uploader_id')
        return [FetchedDoc(info.get('title') or item.title, s.text, [], _date(info),
                           {**meta, 'segment_start_s': s.start_s, 'segment_end_s': s.end_s,
                            'caption_kind': kind, 'segmenter': method},
                           'public', author, f'{s.start_s}-{s.end_s}') for s in segments]
