# 작업 기록

이 문서는 실제 ROM이나 커버 파일을 보관하지 않고, 어떤 규칙과 예외 처리를 적용했는지만 기록합니다.

## 2026-09-14 — 최초 일괄 보완

- `E:\games`에서 NDS ROM 299개 확인
- 고유 게임 코드 280개 확인
- 기존 커버 183개 유지
- 누락된 고유 코드 129개에 커버 추가
- 최종적으로 모든 ROM 코드에 대응하는 커버 존재 여부 확인
- 전체 BMP를 128×96, 8-bit, 무압축, 256색 형식으로 검증
- 오른쪽 22px 영역을 기존 자료와 같은 흰색 패딩으로 통일

예외 처리:

- `C3JK`: DB에 직접 대응하는 커버가 없어 같은 게임인 레이튼 교수 3 일본판 코드 `C3JJ`의 표지를 사용
- `NMB3`: New Super Mario Bros. 3 ROM 핵으로 판단하여 원작 한국판 `A2DK` 커버를 대체 이미지로 사용

## 2026-09-18 — 신규 ROM 4개

- `A6DJ`: Death Note - Kira Game
- `YDNJ`: Death Note - L o Tsugu Mono
- `ASFJ`: Star Fox Command
- `KQ9E`: The Legend of Zelda: Four Swords Anniversary Edition

`KQ9E`는 커버 DB가 범용 DSi Shop 이미지를 반환하여, 게임 로고와 네 명의 링크가 포함된 전용 표지로 수동 교체했습니다.

## 2026-09-20 — 신규 ROM 1개

- `CN8J`: Doki Majo Plus

전용 표지를 생성하고 Pico 규격 및 게임 코드 연결을 검증했습니다.

## DSiWare ZIP 확인

Four Swords Anniversary Edition CDN ZIP의 `00000000`을 검사했습니다.

- 내부 제목: `ZELDA 4SWORD`
- 게임 코드: `KQ9E`
- Unit Code: `3` (DSi 계열)
- 복호화된 SRL/NDS 실행 이미지로 확인
- 이 형식은 `00000000`을 추출하고 `.nds` 확장자를 붙여 사용할 수 있음
- 게임 파일과 타이틀키는 저장소에 포함하지 않음

