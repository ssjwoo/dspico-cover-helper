# DSpico Cover Helper

Pico Launcher에서 Nintendo DS 게임 커버가 표시되도록 누락 커버를 찾아 변환하는 개인용 보조 스크립트입니다.

ROM 파일명 대신 NDS 헤더의 4자리 게임 코드(오프셋 `0x0C`~`0x0F`)를 사용하므로, 한글 패치나 파일명 변경에도 대응합니다.

## 주요 동작

- `E:\games`와 하위 폴더에서 `.nds` 파일 검색
- `E:\_pico\covers\nds`의 기존 커버와 게임 코드 대조
- 누락 커버만 PicoCover 엔드포인트에서 다운로드
- 원본을 106×96으로 축소한 뒤 오른쪽에 22px 흰색 패딩 추가
- 128×96, 8-bit, 256색, 무압축 BMP로 저장
- 기존 커버를 보호하기 위해 `E:\games\_pico\covers\nds`에 먼저 스테이징
- 같은 코드의 커버가 이미 있으면 다운로드 및 덮어쓰기 생략

Pico Launcher 커버 규격은 [공식 Customization 문서](https://github.com/LNH-team/pico-launcher/blob/develop/docs/Customization.md)를 따릅니다.

## 준비

- Windows
- Python 3.10 이상
- Pillow

```powershell
python -m pip install -r requirements.txt
```

## 실행

기본 폴더 구성이 아래와 같을 때 별도 인수 없이 실행할 수 있습니다.

```text
E:\games
E:\_pico\covers\nds
```

```powershell
python fill_pico_covers.py
```

실행 결과는 다음 임시 폴더에 생성됩니다.

```text
E:\games\_pico\covers\nds
```

이미지를 검수한 다음 실제 커버 폴더로 옮겨 사용합니다. 스크립트가 기존 커버를 직접 수정하거나 덮어쓰지는 않습니다.

## 결과 상태

- `saved`: 새 커버를 정상적으로 생성함
- `staged`: 이전 실행에서 생성된 임시 커버가 이미 있음
- `http-404`: 커버 서비스에 해당 게임 코드가 없음
- `network-*`: 네트워크 연결 실패
- `image-*`: 받은 파일을 이미지로 변환하지 못함

DB에 없는 패치·홈브루·DSiWare 게임은 같은 게임의 다른 지역 코드나 별도 전용 아트를 수동으로 지정해야 할 수 있습니다.

## 안전 및 저장소 범위

이 저장소는 스크립트와 문서만 보관합니다. ROM, DSiWare 콘텐츠, 타이틀키, 압축 파일, 생성된 커버 이미지는 포함하지 않으며 `.gitignore`로 커밋을 차단합니다.

## 참고 프로젝트

- [Pico Launcher](https://github.com/LNH-team/pico-launcher)
- [PicoCover](https://github.com/Scaletta/PicoCover)
- [GameTDB](https://www.gametdb.com/)

