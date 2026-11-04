"""여긴어디? 세계 지리 도감 정적 페이지 (Claude, 2026-11-04).

whereisthis 앱의 활성 나라 콘텐츠(지도 설명, 픽셀아트 도감, 대륙·지역 설명)를
검색 로봇이 읽을 수 있는 HTML로 만든다. 앱 웹판은 Flutter 캔버스라 글이 읽히지 않는다.

  /tmp/whereisthis-jo-venv/bin/python tools/build_atlas.py --src /mnt/c/hona/project/whereisthis

- 글과 그림은 whereisthis 저장소 HEAD 기준이다(출시된 앱과 같다).
  작업 트리에서 바뀐 파일은 HEAD 판을 읽는다.
- 그림은 줄여서 atlas/img/에 둔다: 도감 448px, 지도 긴 변 1000px, WebP q72.
  이미 있으면 다시 만들지 않는다(--force로 다시 만듦).
- 결과: atlas/(한국어), en/atlas/(영어), sitemap.xml
- 필요: Pillow
"""
import argparse
import html
import io
import json
import subprocess
from datetime import date
from pathlib import Path

from PIL import Image

SITE = Path(__file__).resolve().parents[1]
BASE = 'https://yenalab.com'


def clean(path):
    """Cloudflare가 .html 주소를 확장자 없는 주소로 넘긴다(307). 대표 주소는 넘어간 뒤의 주소다."""
    if path.endswith('index.html'):
        return path[:-len('index.html')]
    return path[:-5] if path.endswith('.html') else path
ADS = ('<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js'
       '?client=ca-pub-6576535388233153" crossorigin="anonymous"></script>')
CONTINENTS = ['AS', 'EU', 'AF', 'NA', 'SA', 'OC']
CATEGORIES = ['city', 'heritage', 'nature', 'flora', 'culture', 'food', 'animal', 'language', 'flag']
SQUARE = {'PL': 'poland-v1', 'HU': 'hungary-v1', 'GH': 'ghana-v1', 'NG': 'nigeria-v1',
          'CM': 'cameroon-v1', 'CU': 'cuba-v1', 'JM': 'jamaica-v1'}
MAP_DIRS = ['natural-plains-v1', 'africa-oceania-v1', 'south-america-v1', 'north-america-v1']

T = {
    'ko': {
        'lang': 'ko', 'brand': '예나랩', 'app': '여긴어디?', 'atlas': '세계 지리 도감',
        'nav_atlas': '도감', 'nav_apps': '앱', 'nav_contact': '문의', 'switch': '🇺🇸 EN',
        'cats': {'city': '도시', 'heritage': '역사유산', 'nature': '자연', 'flora': '식물',
                 'culture': '문화', 'food': '음식', 'animal': '동물', 'language': '인사말', 'flag': '국기'},
        'capital': '수도', 'population': '인구', 'area': '넓이', 'language': '공용어',
        'map_h': '지도로 읽는 풍경', 'map_alt': '{name} 그림 지도',
        'map_credit': '그림 지도: 예나랩. 나라 윤곽: Natural Earth(공공 영역).',
        'dokam_h': '도감', 'dokam_lead': '{name}에서 잘 알려진 도시, 역사유산, 자연, 식물, 문화, 음식, 동물, 인사말, 국기를 한 장씩 그렸어요.',
        'sources_h': '참고한 자료', 'source': '출처',
        'related_h': '같은 지역의 다른 나라', 'regions_h': '지역', 'countries_h': '나라',
        'home': '도감 처음으로', 'app_page': '앱 소개', 'privacy': '개인정보처리방침',
        'lab_home': '예나랩 홈', 'footer_copy': '단서를 따라 나라를 발견하는 세계 지리 탐험 앱',
        'title_country': '{name}의 지형과 도감 | 여긴어디? 세계 지리 도감',
        'title_continent': '{name}의 지형과 나라 | 여긴어디? 세계 지리 도감',
        'title_index': '여긴어디? 세계 지리 도감 | 예나랩',
        'index_eyebrow': 'World Geography Atlas',
        'index_lead': ('어린이 세계 지리 앱 「여긴어디?」에 담긴 나라 이야기를 웹에서도 읽을 수 있게 모았습니다. '
                       '나라마다 그림 지도로 읽는 땅의 모습과, 도시·역사유산·자연·식물·문화·음식·동물·인사말·국기 '
                       '아홉 갈래의 도감을 실었습니다.'),
        'stats': [('대륙', None), ('나라', None), ('도감 항목', None)],
        'about_h': '이 도감은 이렇게 만들었습니다',
        'about': [
            ('지도 설명', '지리학자의 눈으로 땅이 어떻게 만들어졌는지(판의 충돌, 화산, 빙하, 강의 퇴적)와 어디에 있는지를 씁니다. '
                        '높이·길이·넓이 같은 숫자는 정부 기관, 국제기구, 학술 기관 자료로 확인하고 출처를 함께 적습니다.'),
            ('도감 설명', '항목마다 그 분야를 연구하는 사람의 관점으로 씁니다. 도시는 도시지리, 역사유산은 건축사와 고고학, '
                        '자연은 지질과 지형, 동물은 동물생태의 관점입니다. 처음에는 쉬운 설명을, 이어서 자세한 설명을 둡니다.'),
            ('그림', '픽셀아트 그림과 그림 지도는 예나랩이 앱을 위해 만들었습니다. 지도 윤곽과 국경은 Natural Earth 공개 자료를 따릅니다.'),
            ('쓰지 않는 것', '정치적 판단이나 진행 중인 나라 사이의 분쟁은 다루지 않습니다. 역사는 확인된 사실만 짧게 씁니다.'),
            ('바로잡기', '틀린 내용을 발견하면 official@yenalab.com으로 알려 주세요. 확인한 뒤 앱과 이 도감을 함께 고칩니다.'),
        ],
        'continents_h': '대륙별로 둘러보기', 'all_h': '모든 나라',
        'continent_link': '{name} 지형과 나라 보기',
        'country_count': '나라 {n}곳',
        'app_cta': '앱에서 탐험하기', 'app_cta_text': '「여긴어디?」 앱에서는 단서를 따라 나라를 직접 발견하고, 국기와 수도 퀴즈로 복습할 수 있습니다.',
    },
    'en': {
        'lang': 'en', 'brand': 'yenalab', 'app': 'Where Is This?', 'atlas': 'World Geography Atlas',
        'nav_atlas': 'Atlas', 'nav_apps': 'Apps', 'nav_contact': 'Contact', 'switch': '🇰🇷 KO',
        'cats': {'city': 'City', 'heritage': 'Heritage', 'nature': 'Nature', 'flora': 'Plants',
                 'culture': 'Culture', 'food': 'Food', 'animal': 'Animals', 'language': 'Greeting', 'flag': 'Flag'},
        'capital': 'Capital', 'population': 'Population', 'area': 'Area', 'language': 'Language',
        'map_h': 'Reading the land', 'map_alt': 'Illustrated map of {name}',
        'map_credit': 'Illustrated map: yenalab. Country outlines: Natural Earth (public domain).',
        'dokam_h': 'Collection', 'dokam_lead': 'A city, a heritage site, nature, a plant, culture, food, an animal, a greeting and the flag of {name}, each drawn as pixel art.',
        'sources_h': 'Sources', 'source': 'Source',
        'related_h': 'More countries in this region', 'regions_h': 'Regions', 'countries_h': 'Countries',
        'home': 'Atlas home', 'app_page': 'About the app', 'privacy': 'Privacy Policy',
        'lab_home': 'yenalab home', 'footer_copy': 'A world geography app where kids discover countries by following clues',
        'title_country': '{name}: landforms and collection | Where Is This? World Geography Atlas',
        'title_continent': '{name}: landforms and countries | Where Is This? World Geography Atlas',
        'title_index': 'Where Is This? World Geography Atlas | yenalab',
        'index_eyebrow': 'World Geography Atlas',
        'index_lead': ('The country stories from the kids’ geography app “Where Is This?”, collected so they can be read on the web. '
                       'Each country has an illustrated map with notes on its landforms, and a nine-part collection: '
                       'city, heritage, nature, plants, culture, food, animals, greeting and flag.'),
        'stats': [('Continents', None), ('Countries', None), ('Collection entries', None)],
        'about_h': 'How this atlas is made',
        'about': [
            ('Map notes', 'Written from a geographer’s point of view: how the land formed (colliding plates, volcanoes, glaciers, river deposits) and where things are. '
                          'Heights, lengths and areas are checked against government, international and academic sources, which are listed with each note.'),
            ('Collection notes', 'Each entry is written from the point of view of its field: urban geography for cities, architectural history and archaeology for heritage, '
                                 'geology and landforms for nature, and animal ecology for animals. An easy version comes first, then the detailed one.'),
            ('Pictures', 'The pixel art and illustrated maps were made by yenalab for the app. Coastlines and borders follow Natural Earth open data.'),
            ('What we leave out', 'Political judgements and ongoing disputes between countries are not covered. History is kept short and limited to confirmed facts.'),
            ('Corrections', 'If you find a mistake, please write to official@yenalab.com. We fix the app and this atlas together.'),
        ],
        'continents_h': 'Browse by continent', 'all_h': 'All countries',
        'continent_link': 'Landforms and countries of {name}',
        'country_count': '{n} countries',
        'app_cta': 'Explore in the app', 'app_cta_text': 'In the “Where Is This?” app, kids discover each country by following clues and review flags and capitals with quizzes.',
    },
}


class Source:
    """whereisthis 저장소 읽기: 작업 트리에서 바뀐 파일은 HEAD 판을 읽는다."""

    def __init__(self, root):
        self.root = Path(root)
        out = subprocess.run(['git', '-C', str(self.root), 'status', '--porcelain'],
                             capture_output=True, text=True, check=True).stdout
        self.dirty = {line[3:].strip() for line in out.splitlines() if line[:2].strip() == 'M'}

    def read(self, rel):
        if rel in self.dirty:
            return subprocess.run(['git', '-C', str(self.root), 'show', f'HEAD:{rel}'],
                                  capture_output=True, check=True).stdout
        return (self.root / rel).read_bytes()

    def json(self, rel):
        return json.loads(self.read(rel).decode('utf-8'))

    def exists(self, rel):
        return (self.root / rel).exists()


def e(text):
    return html.escape(text or '', quote=True)


def save_webp(data, out, long_side, force):
    if out.exists() and not force:
        return Image.open(out).size
    out.parent.mkdir(parents=True, exist_ok=True)
    im = Image.open(io.BytesIO(data)).convert('RGB')
    scale = min(1.0, long_side / max(im.size))
    if scale < 1:
        im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    im.save(out, 'WEBP', quality=72, method=6)
    return im.size


def map_asset(src, code):
    low = code.lower()
    if code in SQUARE:
        return f'assets/maps/illustrated/{SQUARE[code]}/map.webp'
    for d in MAP_DIRS:
        rel = f'assets/maps/illustrated/{d}/{low}.webp'
        if src.exists(rel):
            return rel
    raise FileNotFoundError(f'map for {code}')


class Page:
    """한 언어의 페이지 틀. depth는 사이트 뿌리에서 atlas 폴더까지 깊이다."""

    def __init__(self, lang):
        self.t = T[lang]
        self.lang = lang
        self.root = '../' if lang == 'ko' else '../../'   # atlas/ 또는 en/atlas/에서 사이트 뿌리
        self.hub = '../' if lang == 'ko' else '../'       # 같은 언어의 허브(index.html 있는 곳)
        self.img = '' if lang == 'ko' else '../../atlas/'
        self.other = '../en/atlas/' if lang == 'ko' else '../../atlas/'

    def url(self, name):
        return clean(f'{BASE}/atlas/{name}' if self.lang == 'ko' else f'{BASE}/en/atlas/{name}')

    def head(self, name, title, desc, image=None):
        t = self.t
        ko, en = clean(f'{BASE}/atlas/{name}'), clean(f'{BASE}/en/atlas/{name}')
        og = f'\n  <meta property="og:image" content="{BASE}/atlas/{image}" />' if image else ''
        return f'''<!DOCTYPE html>
<html lang="{t['lang']}">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{e(title)}</title>
  <meta name="description" content="{e(desc)}" />
  <meta property="og:title" content="{e(title)}" />
  <meta property="og:description" content="{e(desc)}" />
  <meta property="og:type" content="article" />{og}
  {ADS}
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="{self.root}colors_and_type.css" />
  <link rel="stylesheet" href="{self.root}style.css" />
  <link rel="stylesheet" href="{self.root}atlas.css" />
  <link rel="canonical" href="{self.url(name)}" />
  <link rel="alternate" hreflang="ko" href="{ko}" />
  <link rel="alternate" hreflang="en" href="{en}" />
  <link rel="alternate" hreflang="x-default" href="{ko}" />
</head>
<body class="atlas-page">
  <nav class="site-nav">
    <div class="nav-inner">
      <a class="nav-logo" href="{self.hub}index.html">{t['brand']}</a>
      <ul class="nav-links">
        <li><a href="index.html">{t['nav_atlas']}</a></li>
        <li><a href="{self.hub}index.html#apps">{t['nav_apps']}</a></li>
        <li><a href="{self.hub}index.html#support">{t['nav_contact']}</a></li>
        <li><a class="nav-lang" href="{self.other}{name}" hreflang="{'en' if self.lang == 'ko' else 'ko'}" lang="{'en' if self.lang == 'ko' else 'ko'}">{t['switch']}</a></li>
      </ul>
    </div>
  </nav>
'''

    def foot(self):
        t = self.t
        return f'''
  <footer class="site-footer">
    <div class="footer-inner">
      <div>
        <div class="footer-brand">{t['app']} {t['atlas']}</div>
        <p class="footer-copy">{t['footer_copy']}</p>
      </div>
      <div class="footer-links">
        <a href="index.html">{t['home']}</a>
        <a href="{self.hub}whereisthis.html">{t['app_page']}</a>
        <a href="{self.hub}whereisthis-privacy.html">{t['privacy']}</a>
        <a href="{self.hub}index.html">{t['lab_home']}</a>
      </div>
    </div>
    <div class="footer-bottom">© 2026 yenalab. All rights reserved.</div>
  </footer>
</body>
</html>
'''


def pick(obj, key, lang):
    return obj.get(key + ('Ko' if lang == 'ko' else 'En')) or obj.get(key + 'Ko') or ''


def notes_html(notes, sources, lang, level='h3'):
    t = T[lang]
    out = []
    for n in notes:
        refs = []
        for k in n.get('sources', []):
            s = sources.get(k)
            if s:
                refs.append(f'<a href="{e(s["url"])}" rel="noopener" target="_blank">{e(s["organization"])}, {e(s["title"])}</a>')
        ref = f'<p class="note-source">{t["source"]}: {" · ".join(refs)}</p>' if refs else ''
        out.append(f'''<article class="note-card">
            <{level}>{e(pick(n, 'title', lang))}</{level}>
            <p>{e(pick(n, 'body', lang))}</p>
            {ref}
          </article>''')
    return '\n          '.join(out)


def source_list(sources, lang):
    items = [f'<li>{e(s["organization"])}, <a href="{e(s["url"])}" rel="noopener" target="_blank">{e(s["title"])}</a></li>'
             for s in sources.values()]
    return f'<ul class="source-list">{"".join(items)}</ul>'


def country_card(c, page, lang):
    name = c['nameKo'] if lang == 'ko' else c['nameEn']
    hint = c['hintKo'] if lang == 'ko' else (c.get('hintEn') or c['hintKo'])
    return f'''<a class="country-card" href="{c['countryCode'].lower()}.html">
            <img src="{page.img}img/flags/{c['countryCode'].lower()}.svg" alt="" width="48" height="32" loading="lazy" />
            <span class="country-card-name">{e(name)}</span>
            <span class="country-card-hint">{e(hint)}</span>
          </a>'''


def build(args):
    src = Source(args.src)
    out_ko, out_en = SITE / 'atlas', SITE / 'en/atlas'
    countries = [c for c in src.json('assets/data/countries.ko.json') if c.get('isActive')]
    countries.sort(key=lambda c: c.get('sortOrder', 0))
    geo_cont = {c: src.json(f'assets/data/geography/continents/{c.lower()}.json') for c in CONTINENTS}
    regions_ko = {r['regionCode']: r for r in src.json('assets/data/regions.ko.json')}
    by_cont = {c: [x for x in countries if x['continentCode'] == c] for c in CONTINENTS}

    def region_name(cont, code, lang):
        r = geo_cont[cont]['readings'].get(code)
        if r:
            return pick(r, 'name', lang)
        return regions_ko[code]['nameKo'] if lang == 'ko' else code.replace('_', ' ').title()

    # 그림
    images, art_total = {}, 0
    for c in countries:
        code = c['countryCode'].lower()
        (SITE / 'atlas/img/flags').mkdir(parents=True, exist_ok=True)
        (SITE / f'atlas/img/flags/{code}.svg').write_bytes(src.read(c['flagAsset']))
        images[code] = {'map': save_webp(src.read(map_asset(src, c['countryCode'])),
                                         SITE / f'atlas/img/maps/{code}.webp', 1000, args.force)}
        dokam = src.json(f'assets/data/pixelarts/{c["continentCode"].lower()}/{code}.json')
        c['_dokam'] = {cat['category']: cat['items'] for cat in dokam['categories']}
        for items in c['_dokam'].values():
            for it in items:
                if it['asset'].endswith('.svg'):   # 국기 항목은 SVG 그대로
                    rel = f'img/art/{code}/{Path(it["asset"]).stem.lower()}.svg'
                    (SITE / 'atlas' / rel).parent.mkdir(parents=True, exist_ok=True)
                    (SITE / 'atlas' / rel).write_bytes(src.read(it['asset']))
                    it['_size'] = (448, 448)
                else:
                    rel = f'img/art/{code}/{Path(it["asset"]).stem}.webp'
                    it['_size'] = save_webp(src.read(it['asset']), SITE / 'atlas' / rel, 448, args.force)
                it['_img'] = rel
                art_total += 1
        c['_geo'] = src.json(f'assets/data/geography/countries/{code}.json')

    pages = []
    for lang, outdir in (('ko', out_ko), ('en', out_en)):
        outdir.mkdir(parents=True, exist_ok=True)
        t = T[lang]
        page = Page(lang)

        # 나라
        for c in countries:
            code = c['countryCode'].lower()
            name = c['nameKo'] if lang == 'ko' else c['nameEn']
            other = c['nameEn'] if lang == 'ko' else c['nameNative']
            geo = c['_geo']
            hint = c['hintKo'] if lang == 'ko' else (c.get('hintEn') or c['hintKo'])
            cont = geo_cont[c['continentCode']]['readings'][c['continentCode']]
            facts = [
                (t['capital'], c['capitalKo'] if lang == 'ko' else (c.get('capitalEn') or c['capitalKo'])),
                (t['population'], c.get('populationKo') if lang == 'ko' else c.get('populationEn')),
                (t['area'], c.get('areaKm2')),
                (t['language'], c.get('officialLanguageKo') if lang == 'ko' else c.get('officialLanguageEn')),
            ]
            facts_html = ''.join(f'<span class="chip"><b>{e(k)}</b> {e(v)}</span>' for k, v in facts if v)
            topics = '\n'.join(f'''        <div class="topic">
          <h3>{e(pick(tp, 'title', lang))}</h3>
          <div class="note-grid">
          {notes_html(tp['notes'], geo['sources'], lang, 'h4')}
          </div>
        </div>''' for tp in geo['topics'])
            cats = []
            for cat in CATEGORIES:
                items = c['_dokam'].get(cat, [])
                cards = '\n'.join(f'''          <article class="art-card">
            <img{' class="art-svg"' if it['_img'].endswith('.svg') else ''} src="{page.img}{it['_img']}" alt="{e(pick(it, 'name', lang))}" width="{it['_size'][0]}" height="{it['_size'][1]}" loading="lazy" />
            <div class="art-body">
              <span class="art-cat">{t['cats'][cat]}</span>
              <h3>{e(pick(it, 'name', lang))}</h3>
              <p class="art-easy">{e(pick(it, 'easyDescription', lang))}</p>
              <p class="art-detail">{e(pick(it, 'description', lang))}</p>
            </div>
          </article>''' for it in items)
                if cards:
                    cats.append(cards)
            region_peers = [x for x in countries if x['regionCode'] == c['regionCode'] and x is not c] or \
                [x for x in by_cont[c['continentCode']] if x is not c]
            related = '\n          '.join(country_card(x, page, lang) for x in region_peers)
            mw, mh = images[code]['map']
            desc = f'{hint} {pick(geo, "easy", lang)}'
            body = f'''
  <header class="subpage-hero atlas-hero">
    <div class="narrow">
      <p class="crumbs"><a href="index.html">{t['atlas']}</a> › <a href="continent-{c['continentCode'].lower()}.html">{e(pick(cont, 'name', lang))}</a> › {e(region_name(c['continentCode'], c['regionCode'], lang))}</p>
      <div class="atlas-title">
        <img class="atlas-flag" src="{page.img}img/flags/{code}.svg" alt="" width="96" height="64" />
        <div>
          <h1>{e(name)}</h1>
          <p class="atlas-sub">{e(other)}</p>
        </div>
      </div>
      <p class="lead">{e(hint)}</p>
      <div class="fact-chips">{facts_html}</div>
    </div>
  </header>

  <main>
    <section class="section atlas-section">
      <div class="narrow">
        <div class="eyebrow">Map</div>
        <h2>{t['map_h']}</h2>
        <figure class="atlas-map">
          <img src="{page.img}img/maps/{code}.webp" alt="{e(t['map_alt'].format(name=name))}" width="{mw}" height="{mh}" />
          <figcaption>{t['map_credit']}</figcaption>
        </figure>
        <p class="atlas-easy">{e(pick(geo, 'easy', lang))}</p>
        <p class="atlas-summary">{e(pick(geo, 'summary', lang))}</p>
{topics}
      </div>
    </section>

    <section class="section atlas-section">
      <div class="narrow">
        <div class="eyebrow">Collection</div>
        <h2>{e(name)} {t['dokam_h']}</h2>
        <p class="atlas-summary">{e(t['dokam_lead'].format(name=name))}</p>
        <div class="art-grid">
{chr(10).join(cats)}
        </div>
      </div>
    </section>

    <section class="section atlas-section">
      <div class="narrow">
        <h2>{t['sources_h']}</h2>
        {source_list(geo['sources'], lang)}
      </div>
    </section>

    <section class="section atlas-section">
      <div class="section-inner">
        <h2>{t['related_h']}</h2>
        <div class="country-grid">
          {related}
        </div>
      </div>
    </section>
  </main>
'''
            (outdir / f'{code}.html').write_text(
                page.head(f'{code}.html', t['title_country'].format(name=name), desc, f'img/maps/{code}.webp') + body + page.foot(),
                encoding='utf-8')
            pages.append(page.url(f'{code}.html'))

        # 대륙
        for cc in CONTINENTS:
            if not by_cont[cc]:
                continue
            g = geo_cont[cc]
            r = g['readings'][cc]
            name = pick(r, 'name', lang)
            regions = []
            for rcode in [k for k in g['readings'] if k != cc]:
                members = [x for x in by_cont[cc] if x['regionCode'] == rcode]
                rr = g['readings'][rcode]
                cards = '\n          '.join(country_card(x, page, lang) for x in members)
                grid = f'<div class="country-grid">\n          {cards}\n        </div>' if members else ''
                regions.append(f'''      <div class="region-block">
        <h3>{e(pick(rr, 'name', lang))}</h3>
        <p class="region-headline">{e(pick(rr, 'headline', lang))}</p>
        <p class="atlas-easy">{e(pick(rr, 'easy', lang))}</p>
        <p class="atlas-summary">{e(pick(rr, 'summary', lang))}</p>
        <div class="note-grid">
          {notes_html(rr.get('notes', []), g['sources'], lang, 'h4')}
        </div>
        {grid}
      </div>''')
            body = f'''
  <header class="subpage-hero atlas-hero">
    <div class="narrow">
      <p class="crumbs"><a href="index.html">{t['atlas']}</a> › {e(name)}</p>
      <h1>{e(name)}</h1>
      <p class="lead">{e(pick(r, 'headline', lang))}</p>
    </div>
  </header>

  <main>
    <section class="section atlas-section">
      <div class="narrow">
        <p class="atlas-easy">{e(pick(r, 'easy', lang))}</p>
        <p class="atlas-summary">{e(pick(r, 'summary', lang))}</p>
        <div class="note-grid">
          {notes_html(r.get('notes', []), g['sources'], lang)}
        </div>
      </div>
    </section>

    <section class="section atlas-section">
      <div class="narrow">
        <div class="eyebrow">Regions</div>
        <h2>{t['regions_h']}</h2>
{chr(10).join(regions)}
      </div>
    </section>

    <section class="section atlas-section">
      <div class="narrow">
        <h2>{t['sources_h']}</h2>
        {source_list(g['sources'], lang)}
      </div>
    </section>
  </main>
'''
            fname = f'continent-{cc.lower()}.html'
            (outdir / fname).write_text(
                page.head(fname, t['title_continent'].format(name=name), pick(r, 'easy', lang)) + body + page.foot(),
                encoding='utf-8')
            pages.append(page.url(fname))

        # 처음
        conts = [cc for cc in CONTINENTS if by_cont[cc]]
        stats = [len(conts), len(countries), art_total]
        stat_html = ''.join(f'<div><strong>{n}</strong><span>{lbl}</span></div>' for (lbl, _), n in zip(t['stats'], stats))
        about = ''.join(f'''
          <article class="info-card">
            <h3>{e(h)}</h3>
            <p>{e(p)}</p>
          </article>''' for h, p in t['about'])
        cont_cards = ''.join(f'''
          <a class="continent-card" href="continent-{cc.lower()}.html">
            <span class="continent-name">{e(pick(geo_cont[cc]['readings'][cc], 'name', lang))}</span>
            <span class="continent-headline">{e(pick(geo_cont[cc]['readings'][cc], 'headline', lang))}</span>
            <span class="continent-easy">{e(pick(geo_cont[cc]['readings'][cc], 'easy', lang))}</span>
            <span class="continent-count">{t['country_count'].format(n=len(by_cont[cc]))}</span>
          </a>''' for cc in conts)
        groups = ''.join(f'''
        <h3 class="group-title">{e(pick(geo_cont[cc]['readings'][cc], 'name', lang))}</h3>
        <div class="country-grid">
          {chr(10).join(country_card(x, page, lang) for x in by_cont[cc])}
        </div>''' for cc in conts)
        body = f'''
  <header class="hero">
    <div class="hero-inner">
      <div class="hero-copy">
        <div class="eyebrow">{t['index_eyebrow']}</div>
        <h1>{t['app']} {t['atlas']}</h1>
        <p>{e(t['index_lead'])}</p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="#countries">{t['all_h']}</a>
          <a class="btn btn-secondary" href="{page.hub}whereisthis.html">{t['app_page']}</a>
        </div>
      </div>
      <div class="hero-aside">
        <div class="glass-card mini-grid atlas-stats">{stat_html}</div>
        <div class="glass-card stack-card">
          <span class="card-kicker">{t['app_cta']}</span>
          <p>{e(t['app_cta_text'])}</p>
        </div>
      </div>
    </div>
  </header>

  <main>
    <section class="section">
      <div class="section-inner">
        <div class="section-heading compact"><div><div class="eyebrow">Continents</div><h2>{t['continents_h']}</h2></div></div>
        <div class="continent-grid">{cont_cards}
        </div>
      </div>
    </section>

    <section id="countries" class="section">
      <div class="section-inner">
        <div class="section-heading compact"><div><div class="eyebrow">Countries</div><h2>{t['all_h']}</h2></div></div>{groups}
      </div>
    </section>

    <section class="section">
      <div class="section-inner">
        <div class="section-heading compact"><div><div class="eyebrow">About</div><h2>{t['about_h']}</h2></div></div>
        <div class="feature-grid">{about}
        </div>
      </div>
    </section>
  </main>
'''
        (outdir / 'index.html').write_text(
            page.head('index.html', t['title_index'], t['index_lead']) + body + page.foot(), encoding='utf-8')
        pages.append(page.url('index.html'))

    # sitemap: 기존 허브 페이지 + 도감
    hub = sorted(p.name for p in SITE.glob('*.html'))
    urls = [clean(f'{BASE}/{n}') for n in hub]
    urls += [clean(f'{BASE}/en/{n}') for n in sorted(p.name for p in (SITE / 'en').glob('*.html'))]
    today = date.today().isoformat()
    xml = ''.join(f'  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n' for u in urls + pages)
    (SITE / 'sitemap.xml').write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{xml}</urlset>\n',
        encoding='utf-8')
    print(json.dumps({'countries': len(countries), 'artImages': art_total, 'pages': len(pages),
                      'sitemapUrls': len(urls) + len(pages), 'dirtyReadFromHead': sorted(src.dirty & {
                          map_asset(src, c['countryCode']) for c in countries})}, ensure_ascii=False))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True, help='whereisthis 저장소 경로')
    ap.add_argument('--force', action='store_true', help='그림을 다시 만든다')
    build(ap.parse_args())
