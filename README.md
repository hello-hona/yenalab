# yenalab

![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)
![Cloudflare](https://img.shields.io/badge/Cloudflare-F38020?style=flat-square&logo=cloudflare&logoColor=white)
![i18n](https://img.shields.io/badge/i18n-KO%20%7C%20EN-111111?style=flat-square)
![License](https://img.shields.io/badge/license-All%20rights%20reserved-lightgrey?style=flat-square)

예나랩(yenalab)이 만드는 앱들의 브랜드 허브 사이트. 앱 소개와 앱별 정책 문서(개인정보처리방침, 이용약관, 계정 삭제 안내)를 정적 페이지로 운영한다.

**Live**: https://yenalab.com

## 기술 스택

| 영역 | 사용 기술 |
|------|-----------|
| 마크업/스타일 | 순수 HTML + CSS (빌드 도구 없음) |
| 스크립트 | Vanilla JS (index의 앱 카테고리 필터만 사용) |
| 디자인 토큰 | `colors_and_type.css` — 색상/타이포/간격 CSS 변수 |
| 폰트 | Noto Sans KR (Google Fonts, 400/500/700) |
| 호스팅 | Cloudflare Workers (main 브랜치 자동 배포) |
| 광고 | Google AdSense (`ads.txt`, `app-ads.txt`) |

## 구조

```
/                        # 한국어 (기본)
├── index.html           # 메인 허브: 앱 디렉터리 + 정책 구조 + 지원
├── privacy.html         # 개인정보처리방침 허브 (앱별 문서로 연결)
├── <app>.html           # 앱 소개 (sem-onestep, whereisthis, yenadoku)
├── <app>-privacy.html   # 앱별 개인정보처리방침
├── <app>-terms.html     # 앱별 이용약관
├── account-deletion.html# 셈한걸음 계정 삭제 안내 (Google Play 등록용)
├── colors_and_type.css  # 디자인 토큰
├── style.css            # 컴포넌트 스타일
└── en/                  # 영어 (한국어와 1:1 동일 구조)
```

## 다국어 (i18n)

- **디렉터리 방식**: 한국어는 루트, 영어는 `/en/`. JS 런타임 번역 없음.
- 모든 페이지에 `hreflang`(ko/en/x-default) 상호 연결. `x-default`는 한국어.
- nav 오른쪽 언어 스위처(🇺🇸 EN / 🇰🇷 KO)로 같은 페이지의 상대 언어 버전 이동.
- **언어 추가 절차**: `en/` 폴더 복사 → 텍스트 번역 → 각 페이지 `hreflang`에 한 줄 추가.

## 규칙

- **정책 URL 변경 금지** — `*-privacy.html`, `*-terms.html`, `account-deletion.html`은 스토어 등록정보에서 참조하므로 파일명/경로를 바꾸지 않는다.
- **브랜드 표기** — 영어는 항상 소문자 `yenalab`, 한국어는 `예나랩`.
- **앱 추가 시** — `index.html` 앱 카드, `privacy.html` 카드, 앱 소개/정책 페이지 생성, `en/`에 동일 반영. nav/footer는 수정 불필요.
- 절대 URL은 `https://yenalab.com` 기준.

## 로컬 확인

빌드 없음. 파일을 브라우저로 열거나 정적 서버로 확인:

```bash
npx serve .
```
