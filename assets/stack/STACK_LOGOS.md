# Stack logos — 정적 배지 및 출처

확인일: 2026-11-25. 이 디렉터리는 README와 오프라인 미리보기에서 사용할 실제 브랜드 마크 배지를 포함한다. 외부 Shields/CDN 요청 없이 SVG 또는 PNG 파일만으로 표시된다.

## 시각 규격

- 공통 논리 높이: 32px. 패널 `#111C29`, 경계 `#34495E`, 글자 `#F0F6FC`, 모서리 6px.
- 왼쪽 20×20px 로고의 경로·비율은 Simple Icons 원본 그대로다. 마스코트나 임의 코드 기호로 대체하지 않았다.
- 기본 로고 색은 고정 커밋의 Simple Icons 메타데이터 `hex`. 검정 계열 GitHub/MCP만 어두운 패널에서 보이도록 `#F0F6FC` 단색으로 표시한다.
- SVG는 편집 가능한 코드 원본이며 내부에 경로가 들어 있다. 외부 이미지·스크립트·폰트 URL은 없다.
- PNG는 2배 해상도이고 둥근 모서리 바깥만 투명하다. 밝은·어두운 GitHub 테마 모두 같은 불투명 패널을 쓴다.
- Google Apps Script는 `googleappsscript`, MCP는 `modelcontextprotocol`, 최신 CSS는 `css` 슬러그를 실제로 확인했다.

## 배치

Core 6개, Web & tools 4개, Workspace 4개, Other projects 5개의 네 그룹으로 구성한다. Other projects는 README에서 “다른 프로젝트에서 사용” 항목으로 표시한다. 좁은 화면에서는 자연스럽게 줄이 바뀌게 하고 표 안에 배지를 강제로 넣지 않는다. 위아래 애니메이션과 경쟁하지 않도록 배지 자체에는 모션을 넣지 않는다.

| 범주 | 파일 stem | 표시명 | README 폭×높이 | PNG 픽셀 |
|---|---|---|---|---|
| Core | python | Python | 96×32 | 192×64 |
| Core | javascript | JavaScript | 116×32 | 232×64 |
| Core | typescript | TypeScript | 118×32 | 236×64 |
| Core | nodejs | Node.js | 99×32 | 198×64 |
| Core | postgresql | PostgreSQL | 125×32 | 250×64 |
| Core | google-apps-script | Apps Script | 124×32 | 248×64 |
| Web & tools | html5 | HTML5 | 95×32 | 190×64 |
| Web & tools | css | CSS | 84×32 | 168×64 |
| Web & tools | github | GitHub | 96×32 | 192×64 |
| Web & tools | mcp | MCP | 84×32 | 168×64 |
| Workspace | google-sheets | Sheets | 95×32 | 190×64 |
| Workspace | google-docs | Docs | 84×32 | 168×64 |
| Workspace | google-drive | Drive | 85×32 | 170×64 |
| Workspace | discord | Discord | 99×32 | 198×64 |
| Other projects | react | React | 87×32 | 174×64 |
| Other projects | vite | Vite | 84×32 | 168×64 |
| Other projects | supabase | Supabase | 114×32 | 228×64 |
| Other projects | fastapi | FastAPI | 97×32 | 194×64 |
| Other projects | svelte | Svelte | 91×32 | 182×64 |

배지 그룹은 README의 표시 구분이며 숙련도를 나타내지 않는다. React·Vite·Supabase·FastAPI·Svelte도 기존 배지와 같은 높이·패널·서체를 사용한다. 추가된 로고의 형태와 색은 아래 고정 커밋의 원본 및 메타데이터를 따른다.

## 사용 예

```html
<img src="./assets/stack/python.png" width="96" height="32" alt="Python" />
<img src="./assets/stack/google-apps-script.png" width="124" height="32" alt="Google Apps Script" />
<img src="./assets/stack/mcp.png" width="84" height="32" alt="Model Context Protocol" />
```

README의 기본은 PNG다. 같은 stem의 SVG는 편집·선택용 원본으로 보관한다. PNG의 2배 픽셀 크기를 그대로 HTML width로 넣지 않는다. 재현 코드를 옮길 때는 이 디렉터리의 `badge-config.json`과 `vendor/`도 함께 복사한다.

## 원본·출처

브랜드 형상의 공급원: [Simple Icons 공식 저장소](https://github.com/simple-icons/simple-icons). Simple Icons는 브랜드 공식 계정과 별개의 아이콘 프로젝트다. 아래는 이 프로젝트가 수집한 브랜드 마크로, 공식 제휴나 인증을 뜻하지 않는다.

단일 고정 커밋: `d59bb32d4f94b1aa8c7cef9d264280d35d5f8f97` (`develop`, 조회 시점). `badge-config.json`과 `manifest.json`에 아이콘별 원본 blob SHA, 출처 URL, 브랜드별 source/guidelines/license 메타데이터를 담았다.

| 브랜드 | Simple Icons 파일 | 브랜드 출처 |
|---|---|---|
| Python | [python.svg](https://github.com/simple-icons/simple-icons/blob/d59bb32d4f94b1aa8c7cef9d264280d35d5f8f97/icons/python.svg) | [source](https://www.python.org/community/logos/) |
| JavaScript | [javascript.svg](https://github.com/simple-icons/simple-icons/blob/d59bb32d4f94b1aa8c7cef9d264280d35d5f8f97/icons/javascript.svg) | [source](https://github.com/voodootikigod/logo.js/blob/1544bdeed6d618a6cfe4f0650d04ab8d9cfa76d9/js.svg) |
| TypeScript | [typescript.svg](https://github.com/simple-icons/simple-icons/blob/d59bb32d4f94b1aa8c7cef9d264280d35d5f8f97/icons/typescript.svg) | [source](https://www.typescriptlang.org/branding) |
| Node.js | [nodedotjs.svg](https://github.com/simple-icons/simple-icons/blob/d59bb32d4f94b1aa8c7cef9d264280d35d5f8f97/icons/nodedotjs.svg) | [source](https://nodejs.org/en/about/branding) |
| PostgreSQL | [postgresql.svg](https://github.com/simple-icons/simple-icons/blob/d59bb32d4f94b1aa8c7cef9d264280d35d5f8f97/icons/postgresql.svg) | [source](https://wiki.postgresql.org/wiki/Logo) |
| Google Apps Script | [googleappsscript.svg](https://github.com/simple-icons/simple-icons/blob/d59bb32d4f94b1aa8c7cef9d264280d35d5f8f97/icons/googleappsscript.svg) | [source](https://github.com/simple-icons/simple-icons/issues/3556#issuecomment-800482267) |
| HTML5 | [html5.svg](https://github.com/simple-icons/simple-icons/blob/d59bb32d4f94b1aa8c7cef9d264280d35d5f8f97/icons/html5.svg) | [source](https://www.w3.org/html/logo/) |
| CSS | [css.svg](https://github.com/simple-icons/simple-icons/blob/d59bb32d4f94b1aa8c7cef9d264280d35d5f8f97/icons/css.svg) | [source](https://github.com/CSS-Next/logo.css/blob/bacc20878227204b283c68a6b935f8279e06b0cd/css.svg) |
| GitHub | [github.svg](https://github.com/simple-icons/simple-icons/blob/d59bb32d4f94b1aa8c7cef9d264280d35d5f8f97/icons/github.svg) | [source](https://github.com/logos) |
| Model Context Protocol | [modelcontextprotocol.svg](https://github.com/simple-icons/simple-icons/blob/d59bb32d4f94b1aa8c7cef9d264280d35d5f8f97/icons/modelcontextprotocol.svg) | [source](https://github.com/modelcontextprotocol/docs/blob/573dc60c2e7aab2605b29d0bf27194aa7b02e4fb/logo/light.svg) |
| Google Sheets | [googlesheets.svg](https://github.com/simple-icons/simple-icons/blob/d59bb32d4f94b1aa8c7cef9d264280d35d5f8f97/icons/googlesheets.svg) | [source](https://sheets.google.com) |
| Google Docs | [googledocs.svg](https://github.com/simple-icons/simple-icons/blob/d59bb32d4f94b1aa8c7cef9d264280d35d5f8f97/icons/googledocs.svg) | [source](https://www.google.com/docs/about) |
| Google Drive | [googledrive.svg](https://github.com/simple-icons/simple-icons/blob/d59bb32d4f94b1aa8c7cef9d264280d35d5f8f97/icons/googledrive.svg) | [source](https://developers.google.com/drive/web/branding) |
| Discord | [discord.svg](https://github.com/simple-icons/simple-icons/blob/d59bb32d4f94b1aa8c7cef9d264280d35d5f8f97/icons/discord.svg) | [source](https://discord.com/branding) |
| React | [react.svg](https://github.com/simple-icons/simple-icons/blob/d59bb32d4f94b1aa8c7cef9d264280d35d5f8f97/icons/react.svg) | [source](https://github.com/facebook/create-react-app/blob/282c03f9525fdf8061ffa1ec50dce89296d916bd/test/fixtures/relative-paths/src/logo.svg) |
| Vite | [vite.svg](https://github.com/simple-icons/simple-icons/blob/d59bb32d4f94b1aa8c7cef9d264280d35d5f8f97/icons/vite.svg) | [source](https://github.com/voidzero-dev/community-design-resources/blob/55902097229cf01cf2a4ceb376f992f5cf306756/brand-assets/vite/vite-icon-color-bracketless.svg) |
| Supabase | [supabase.svg](https://github.com/simple-icons/simple-icons/blob/d59bb32d4f94b1aa8c7cef9d264280d35d5f8f97/icons/supabase.svg) | [source](https://github.com/supabase/supabase/blob/4031a7549f5d46da7bc79c01d56be4177dc7c114/packages/common/assets/images/supabase-logo-wordmark--light.svg) |
| FastAPI | [fastapi.svg](https://github.com/simple-icons/simple-icons/blob/d59bb32d4f94b1aa8c7cef9d264280d35d5f8f97/icons/fastapi.svg) | [source](https://github.com/tiangolo/fastapi/blob/ffb4f77a11f83132b521ba0aac6c95792c19e797/docs/en/docs/img/icon-white.svg) |
| Svelte | [svelte.svg](https://github.com/simple-icons/simple-icons/blob/d59bb32d4f94b1aa8c7cef9d264280d35d5f8f97/icons/svelte.svg) | [source](https://github.com/sveltejs/branding/blob/c4dfca6743572087a6aef0e109ffe3d95596e86a/svelte-logo.svg) |

## 라이선스 보관

- Simple Icons 배포 라이선스는 CC0 1.0 Universal이며, 원문을 `vendor/LICENSE.simple-icons.md`에 보관했다. Git blob SHA `70d4a7b6740c5d9b594ff2fc27d3ea7e89413185`.
- Simple Icons의 개별 브랜드·상표 관련 안내 원문은 `vendor/DISCLAIMER.simple-icons.md`에 있다. Git blob SHA `49f239e6400ca3d10932e34f5bf52a8f883f88e5`. 패키지 CC0가 모든 브랜드의 별도 권리까지 없앤다는 뜻은 아니다.
- JavaScript 마크는 메타데이터에서 MIT로 표시된다. 원본 [logo.js LICENSE](https://github.com/voodootikigod/logo.js/blob/1544bdeed6d618a6cfe4f0650d04ab8d9cfa76d9/LICENSE)를 `vendor/LICENSE.javascript.txt`에 함께 보관했다. 원본 commit `1544bdeed6d618a6cfe4f0650d04ab8d9cfa76d9`, blob `cd1529baebbbb5a7f950e63e1c7ea0af6e982e86`.
- 다른 항목에 별도 license 필드가 없다는 것을 무제한 사용 허가로 해석하지 않는다. 해당 source/guidelines 링크를 manifest에 유지한다.

## 다시 만들기

프로젝트 루트에서:

```sh
python scripts/render_stack_badges.py
```

Python 3, Pillow, Inkscape가 필요하다. 생성은 오프라인이다. 스크립트는 vendored SVG를 기록된 Git blob SHA와 대조하고, 허용된 path만 배지에 넣고, SVG와 2x PNG 및 해시 manifest를 작성한다. Inkscape가 PATH에 없으면 `--inkscape`로 실행 파일을 지정한다. 검수용 밝은·어두운 배경 그림의 저장 위치는 `--preview-output 경로`로 지정할 수 있다. 네 그룹 모두 설정 파일에서 읽는다.

## 수행한 검수

- 19개 로고 원본의 Git blob SHA가 소스 반환 SHA와 정확히 일치.
- 19개 SVG XML 파싱 및 path 원본 좌표 유지.
- 모든 배지 높이 32px, 각 라벨에 맞춘 가변 폭.
- PNG 19개가 RGBA 및 지정된 2배 크기인지 확인. 바깥 모서리는 alpha=0.
- 추가 작업 전후 기존 14개 배지의 SVG·PNG 해시는 동일하다.
- 검수 그림에서 네 그룹을 밝은/어두운 배경의 실제 1배 크기로 눈으로 확인: 잘린 텍스트 없음, 심볼 및 글자 겹침 없음.
- 이 검수는 로컬 산출물 검수다. GitHub 실제 배포 페이지 렌더 확인은 프로필 반영 단계에서 수행한다.

