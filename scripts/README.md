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
| `assets/divider/trail.gif` | 960×72, 16초 루프. 작은 문서를 따라 움직이는 정령 | `render_divider.py` |
| `assets/profile/footer.gif` | 960×112, 16초 루프. 잠든 동료들의 호흡, 정령과 랜턴 | `render_banners.py` |
| `assets/stack/*.png` | 브랜드 로고와 도구 이름을 함께 표시하는 정적 배지 | `render_stack_badges.py` |

렌더 스크립트를 실행하면 검수용 미리보기 이미지와 JSON 보고서도 생성된다.

세 GIF에는 같은 파일명의 **PNG 정지 대안**이 있다. 움직임을 사용하지 않으려면 README의 해당 경로를 `header.png`, `trail.png`, `footer.png`로 바꾸면 된다. 함께 있는 SVG는 정지 프레임이며, 시간에 따른 움직임은 Python 렌더러에서 만든다.

펫 원본과 팔레트는 `assets/source/`에 있다. 로고 원본·배지 설정·라이선스는 `assets/stack/vendor/`, `badge-config.json`에 보관한다. 렌더러는 이 로컬 원본을 사용하며 외부 이미지 요청 없이 결과를 만든다.

## 로고 출처

배지의 브랜드 마크는 [Simple Icons](https://github.com/simple-icons/simple-icons)에서 가져왔다. 아이콘별 원본·브랜드 출처·라이선스는 [STACK_LOGOS.md](../assets/stack/STACK_LOGOS.md)에 정리되어 있다. [Simple Icons 라이선스](../assets/stack/vendor/LICENSE.simple-icons.md), [브랜드 관련 안내](../assets/stack/vendor/DISCLAIMER.simple-icons.md), [JavaScript 마크 라이선스](../assets/stack/vendor/LICENSE.javascript.txt)를 함께 유지한다.
