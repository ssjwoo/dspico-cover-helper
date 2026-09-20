r"""Pico Launcher용 Nintendo DS 커버를 내려받아 임시 폴더에 생성한다.

처리 흐름
1. ``E:\games`` 아래의 모든 ``.nds`` 파일을 찾는다.
2. 각 ROM 헤더에서 4자리 게임 코드를 읽는다.
3. ``E:\_pico\covers\nds``에 해당 코드의 커버가 있는지 확인한다.
4. 없는 커버만 다운로드하여 Pico 규격의 BMP로 변환한다.
5. 결과는 검수할 수 있도록 ``E:\games\_pico\covers\nds``에 저장한다.

주의: 이 스크립트는 안전을 위해 기존 커버 폴더에 직접 덮어쓰지 않는다.
검수한 BMP를 실제 커버 폴더로 옮기는 단계는 별도로 수행해야 한다.
"""

from __future__ import annotations

# 메모리 안에 받은 이미지 데이터를 파일처럼 Pillow에 전달할 때 사용한다.
import io
# 임시 파일을 완성된 BMP 파일로 원자적으로 교체할 때 사용한다.
import os
# 프로그램 종료 코드를 운영체제에 반환할 때 사용한다.
import sys
# 별도 라이브러리 없이 HTTPS로 커버 이미지를 받을 때 사용한다.
import urllib.error
import urllib.request
# 여러 커버를 동시에 다운로드하여 전체 처리 시간을 줄인다.
from concurrent.futures import ThreadPoolExecutor, as_completed
# Windows 경로를 문자열보다 안전하고 읽기 쉽게 다룬다.
from pathlib import Path

# 이미지 열기, 크기 변경, 색상 축소, BMP 저장을 담당한다.
from PIL import Image


# 검사할 NDS ROM 폴더이다. 하위 폴더까지 재귀적으로 검색한다.
GAMES_DIR = Path(r"E:\games")

# 이미 설치되어 있는 Pico Launcher 커버 폴더이다.
# 이곳의 파일명과 대조하여 기존 커버는 다시 만들지 않는다.
COVERS_DIR = Path(r"E:\_pico\covers\nds")

# 새 커버를 바로 설치하지 않고 먼저 저장하는 검수용 임시 폴더이다.
STAGE_DIR = GAMES_DIR / "_pico" / "covers" / "nds"

# 게임 코드에 맞는 NDS 커버를 찾아 돌려주는 PicoCover 엔드포인트이다.
# ``{code}`` 자리는 실행 시 A2DK 같은 실제 게임 코드로 바뀐다.
ENDPOINT = "https://picocover.retrosave.games/nds/{code}"

# Pico Launcher가 읽는 전체 이미지 크기이다.
COVER_SIZE = (128, 96)

# 실제 커버가 들어가는 영역이다. 오른쪽 22픽셀은 UI용 여백으로 남긴다.
ART_SIZE = (106, 96)

# 동시에 실행할 다운로드 작업 수이다.
MAX_WORKERS = 8


def rom_code(path: Path) -> str | None:
    """NDS ROM 헤더에서 4자리 게임 코드를 읽어 대문자로 반환한다.

    Nintendo DS ROM의 게임 코드는 파일 시작점 기준 0x0C~0x0F에 있다.
    파일이 너무 짧거나 코드가 영문/숫자 4자리가 아니면 ``None``을 반환한다.
    """

    # ROM 전체를 읽을 필요가 없으므로 헤더에 필요한 첫 16바이트만 읽는다.
    with path.open("rb") as handle:
        header = handle.read(16)

    # 정상적인 헤더를 읽지 못한 파일은 처리 대상에서 제외한다.
    if len(header) != 16:
        return None

    # 0x0C부터 4바이트가 A2DK 같은 게임 코드이다.
    raw = header[0x0C:0x10]

    # Pico의 코드 기반 커버명으로 사용할 수 없는 값인지 검사한다.
    if not all(value < 128 and chr(value).isalnum() for value in raw):
        return None

    # 파일명 비교가 일정하도록 ASCII 문자열을 대문자로 통일한다.
    return raw.decode("ascii").upper()


def make_cover(code: str) -> tuple[str, str]:
    """게임 코드 하나의 커버를 다운로드하고 Pico 규격 BMP로 변환한다.

    반환값은 ``(게임 코드, 처리 상태)``이다. 처리 상태는 ``saved``,
    ``staged``, ``http-404``, ``network-...``, ``image-...`` 중 하나이다.
    """

    # Pico는 ``<게임코드>.bmp`` 형식의 파일명을 사용한다.
    destination = STAGE_DIR / f"{code}.bmp"

    # 이전 실행에서 이미 만들어 둔 파일은 다시 다운로드하지 않는다.
    if destination.exists():
        return code, "staged"

    # 게임 코드를 URL에 넣고, 서비스에서 요청 주체를 식별할 수 있게
    # 간단한 User-Agent 헤더를 붙인다.
    request = urllib.request.Request(
        ENDPOINT.format(code=code),
        headers={"User-Agent": "Codex-PicoCover/1.0"},
    )

    try:
        # 응답이 무한정 멈추지 않도록 30초 제한을 두고 이미지 바이트를 받는다.
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read()
    except urllib.error.HTTPError as exc:
        # 404 등 서버가 돌려준 HTTP 상태 코드를 결과에 남긴다.
        return code, f"http-{exc.code}"
    except Exception as exc:  # noqa: BLE001 - ROM마다 실패 사유만 기록하고 계속 진행
        # DNS, 연결 시간 초과 같은 네트워크 예외도 전체 작업을 중단시키지 않는다.
        return code, f"network-{type(exc).__name__}"

    try:
        # 메모리에 있는 JPEG/PNG 데이터를 Pillow 이미지로 연다.
        with Image.open(io.BytesIO(payload)) as source:
            # 투명도나 흑백 이미지도 동일하게 처리하도록 RGB로 통일한다.
            rgb = source.convert("RGB")
            # Pico의 실제 표시 영역 106×96에 맞춘다.
            # LANCZOS는 작은 크기로 줄일 때 글자와 윤곽을 비교적 선명하게 보존한다.
            resized = rgb.resize(ART_SIZE, Image.Resampling.LANCZOS)

        # 전체 128×96 캔버스를 흰색으로 만들고 왼쪽에 커버를 붙인다.
        # 따라서 오른쪽 22픽셀은 기존 커버들과 같은 흰색 패딩이 된다.
        canvas = Image.new("RGB", COVER_SIZE, (255, 255, 255))
        canvas.paste(resized, (0, 0))

        # Pico가 요구하는 8-bit 팔레트 이미지가 되도록 최대 256색으로 줄인다.
        indexed = canvas.quantize(colors=256, method=Image.Quantize.MEDIANCUT)

        # 저장 중 중단되어 불완전한 BMP가 남지 않도록 임시 이름에 먼저 기록한다.
        temporary = destination.with_suffix(".bmp.tmp")
        indexed.save(temporary, format="BMP", bits=8)

        # BMP 저장이 끝난 후에만 최종 파일명으로 교체한다.
        os.replace(temporary, destination)
    except Exception as exc:  # noqa: BLE001 - 손상 이미지도 다른 ROM 처리에 영향 주지 않음
        # 내려받은 데이터가 이미지가 아니거나 변환에 실패한 경우를 기록한다.
        return code, f"image-{type(exc).__name__}"

    return code, "saved"


def main() -> int:
    """ROM 목록을 만들고, 누락 커버를 병렬로 생성한 뒤 요약을 출력한다."""

    # parents=True는 중간의 _pico/covers 폴더도 함께 만들고,
    # exist_ok=True는 폴더가 이미 있어도 오류를 내지 않게 한다.
    STAGE_DIR.mkdir(parents=True, exist_ok=True)

    # 같은 게임 코드의 ROM이 여러 개 있을 수 있으므로
    # 코드별로 해당 파일명 목록을 모은다.
    code_to_names: dict[str, list[str]] = {}
    invalid: list[str] = []

    # rglob을 사용해 GAMES_DIR의 모든 하위 폴더에서 .nds 파일을 찾는다.
    for rom in sorted(GAMES_DIR.rglob("*.nds")):
        code = rom_code(rom)
        if code is None:
            # 정상 게임 코드를 읽지 못한 파일은 나중에 개수로 보고한다.
            invalid.append(str(rom))
            continue
        code_to_names.setdefault(code, []).append(rom.name)

    # 기존 BMP의 확장자를 뺀 이름이 곧 게임 코드이다.
    existing = {path.stem.upper() for path in COVERS_DIR.glob("*.bmp")}

    # ROM 코드 집합에서 기존 커버 코드 집합을 빼면 새로 만들 코드만 남는다.
    missing = sorted(set(code_to_names) - existing)

    # 실제 ROM 수, 고유 게임 코드 수, 누락 코드 수를 먼저 출력한다.
    print(
        f"ROMs={sum(map(len, code_to_names.values()))} "
        f"UniqueCodes={len(code_to_names)} MissingCodes={len(missing)}"
    )

    results: dict[str, str] = {}

    # 최대 8개의 게임을 동시에 처리한다. 각 작업은 make_cover를 호출한다.
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        # Future와 게임 코드를 연결해 두면 완료 순서와 무관하게 추적할 수 있다.
        futures = {pool.submit(make_cover, code): code for code in missing}

        # 제출 순서가 아니라 실제로 끝나는 순서대로 결과를 받는다.
        for future in as_completed(futures):
            code, status = future.result()
            results[code] = status

            # 사람이 어떤 게임이 성공/실패했는지 바로 확인할 수 있게 출력한다.
            print(f"{status:>18} {code} {code_to_names[code][0]}", flush=True)

    # 새로 저장했거나 이전 실행에서 이미 임시 저장된 코드는 성공으로 센다.
    saved = [
        code for code, status in results.items() if status in {"saved", "staged"}
    ]

    # 그 외 상태는 수동 확인이 필요한 실패 항목이다.
    failed = [
        code for code, status in results.items() if status not in {"saved", "staged"}
    ]

    # 전체 결과와 읽을 수 없었던 ROM 수를 요약한다.
    print(f"SavedOrStaged={len(saved)} Failed={len(failed)} Invalid={len(invalid)}")

    # 실패 항목이 있으면 다시 검색하거나 대체 커버를 지정하기 쉽도록 코드만 모아 쓴다.
    if failed:
        print("FAILED_CODES=" + ",".join(sorted(failed)))

    # 0은 스크립트 자체가 정상적으로 끝났다는 운영체제 종료 코드이다.
    return 0


# 다른 파일에서 import할 때는 main을 자동 실행하지 않고,
# 이 파일을 직접 실행했을 때만 전체 작업을 시작한다.
if __name__ == "__main__":
    sys.exit(main())

