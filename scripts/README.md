# 프로필 이미지 재생성

이 저장소의 배너와 펫은 SVG 도형으로 구성되며, README에서는 GIF와 PNG를 사용한다. 배포된 이미지를 그대로 표시할 때는 렌더링 도구를 설치할 필요가 없다.

## 실행

Python 3.11 이상, Pillow 13.0.0, Inkscape CLI, DejaVu Sans 글꼴이 필요하다. Inkscape 실행 파일이 `PATH`에 있어야 한다. 저장소 루트에서 실행한다.

```bash
python -m pip install -r scripts/requirements.txt
python scripts/render_banners.py
python scripts/render_divider.py
python scripts/render_stack_badges.py
```

배너의 정지 프레임만 확인하려면 `python scripts/render_banners.py --poster-only`를 사용한다. 실행 검증 환경은 Linux다. Windows에서는 Python/Conda 환경과 Inkscape의 `bin` 경로를 설정해야 하며, 글꼴이 바뀌면 문자 폭도 달라질 수 있다.

## 이미지와 스크립트

| 이미지 | 내용 | 원본 스크립트 |
|---|---|---|
| `assets/profile/header.gif` | 960×360, 16초 루프. 마법사와 다섯 펫, 별과 반딧불, 작은 주문과 글자 하이라이트 | `render_banners.py` |
| `assets/divider/trail.gif` | 420×88, 8초 루프. 투명 배경 위에서 걷고 뛰고 날아다니는 다섯 동료 | `render_divider.py` |
| `assets/profile/footer.gif` | 960×112, 16초 루프. 잠든 동료들의 호흡, 정령과 랜턴 | `render_banners.py` |
| `assets/stack/*.png` | 브랜드 로고와 도구 이름을 함께 표시하는 정적 배지 | `render_stack_badges.py` |

헤더·푸터 렌더 스크립트를 실행하면 검수용 미리보기 이미지와 JSON 보고서도 생성된다. 중간 펫 이미지는 배경이 투명하며, README에서는 원본 폭인 420px로 표시한다.

세 GIF에는 같은 파일명의 **PNG 정지 대안**이 있다. 움직임을 사용하지 않으려면 README의 해당 경로를 `header.png`, `trail.png`, `footer.png`로 바꾸면 된다. 함께 있는 SVG는 정지 프레임이며, 시간에 따른 움직임은 Python 렌더러에서 만든다.

펫 원본과 팔레트는 `assets/source/`에 있다. 로고 원본·배지 설정·라이선스는 `assets/stack/vendor/`, `badge-config.json`에 보관한다. 렌더러는 이 로컬 원본을 사용하며 외부 이미지 요청 없이 결과를 만든다.

## 로고 출처

배지의 브랜드 마크는 [Simple Icons](https://github.com/simple-icons/simple-icons)에서 가져왔다. 아이콘별 원본·브랜드 출처·라이선스는 [STACK_LOGOS.md](../assets/stack/STACK_LOGOS.md)에 정리되어 있다. [Simple Icons 라이선스](../assets/stack/vendor/LICENSE.simple-icons.md), [브랜드 관련 안내](../assets/stack/vendor/DISCLAIMER.simple-icons.md), [JavaScript 마크 라이선스](../assets/stack/vendor/LICENSE.javascript.txt)를 함께 유지한다.

## 최근 공개 작업 자동 갱신

`update_public_work.py`는 공개 저장소 [operations-automation-lab](https://github.com/koeje1/operations-automation-lab)과 [github-profile-banner-animation](https://github.com/koeje1/github-profile-banner-animation)의 기본 브랜치에서 최근 커밋을 하나씩 가져온다. Python 3.11 이상과 표준 라이브러리만 사용하며, 공개 API 조회에는 토큰이나 추가 패키지가 필요 없다. 두 저장소의 공개 여부와 데이터를 모두 확인한 뒤 결과를 쓴다. API 요청이나 데이터 검증에 실패하면 기존 결과를 보존하고 오류로 종료한다.

저장소 루트에서 직접 갱신하거나, 저장된 공개 데이터로 네트워크 요청 없이 다시 생성할 수 있다.

```bash
python scripts/update_public_work.py
python scripts/update_public_work.py --snapshot assets/activity/public-work.json
```

| 생성 파일 | 내용 |
|---|---|
| `assets/activity/public-work-light.svg` | 밝은 테마용 보드 |
| `assets/activity/public-work-dark.svg` | 어두운 테마용 보드 |
| `assets/activity/public-work.json` | 두 공개 저장소의 검증된 커밋 데이터. 오프라인 재생성 입력으로 사용 |

[`public-work.yml`](../.github/workflows/public-work.yml)은 **한국 시간 10:17과 22:17**에 실행하도록 예약되어 있다. UTC cron은 `17 1,13 * * *`이다. [Actions 실행 페이지](https://github.com/koeje1/koeje1/actions/workflows/public-work.yml)에서 `Run workflow`로 `main`을 수동 실행할 수 있으며, `main`에 `scripts/update_public_work.py` 또는 `.github/workflows/public-work.yml` 변경을 push해도 실행된다. 결과 파일 세 개만 커밋 대상으로 삼고, 내용이 같으면 커밋을 만들지 않는다.

예약 실행은 GitHub Actions 부하로 지연될 수 있으며, 공개 프로필 저장소에 60일 동안 활동이 없으면 예약 워크플로가 자동으로 비활성화될 수 있다([GitHub 공식 schedule 문서](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)).
