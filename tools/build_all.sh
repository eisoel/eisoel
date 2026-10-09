#!/usr/bin/env bash
# 저장소의 모든 기관상징을 다시 만든다.
#   tools/build_all.sh path/to/정부상징체.ttf [출력 폴더, 기본 logos]
set -euo pipefail
FONT=$(realpath "${1:?"사용법: $0 path/to/정부상징체.ttf [출력 폴더]"}")
OUT=$(realpath -m "${2:-$(dirname "$0")/../logos}")
cd "$(dirname "$0")/.."
# 이전 결과물(svg/pdf/png, 구성규정·미리보기 이미지)을 지우고 다시 만든다 — 이름이 바뀐 기관의 파일이 남지 않게
for d in "$OUT" "$OUT/고용노동부" "$OUT/관세청" "$OUT/기관별"; do
    rm -rf "$d/svg" "$d/pdf" "$d/png"
    rm -f "$d"/구성규정_*.png "$d/미리보기.png"
done
B=(python3 tools/build_gov_symbol.py --font "$FONT")
O=$OUT/기관별

# 지방국세청 (1행), 지방고용노동청 (A type), 본부세관 (국영문 Type B)
"${B[@]}" --out "$OUT"
"${B[@]}" --out "$OUT/고용노동부" --type A --parent 고용노동부 --filename "{name} 로고" \
    서울지방고용노동청 중부지방고용노동청 경기지방고용노동청 부산지방고용노동청 \
    대구지방고용노동청 광주지방고용노동청 대전지방고용노동청
"${B[@]}" --out "$OUT/관세청" --type 국영B --filename "{name}" \
    "인천공항본부세관=Incheon Airport Regional Customs" "서울본부세관=Seoul Regional Customs" \
    "부산본부세관=Busan Regional Customs" "인천본부세관=Incheon Regional Customs" \
    "대구본부세관=Daegu Regional Customs" "광주본부세관=Gwangju Regional Customs"

# 개별 기관 — 구성규정 이미지는 명령마다 첫 기관으로 만들어지고, 아래 KEEP 에 있는 것만 남긴다
"${B[@]}" --out "$O" --type 1행 --filename "{name} 로고" 조세심판원 고용보험심사위원회 복권위원회 \
    원주지방국토관리청 서울지방국토관리청 부산지방항공청 제주지방항공청 서울지방항공청 \
    부산지방국토관리청 대전지방국토관리청 익산지방국토관리청
"${B[@]}" --out "$O" --type 1행 --filename "{name} 로고" 공무원재해보상연금위원회 농식품인재개발원
"${B[@]}" --out "$O" --type 1행 --filename "{name} 로고" 국가바이오혁신위원회
"${B[@]}" --out "$O" --type 2행 --filename "{name} 로고" "산업재해보상보험|재심사위원회"
"${B[@]}" --out "$O" --type A --parent 문화체육관광부 --filename "{name} 로고" 국립김해박물관 국립민속국악원
"${B[@]}" --out "$O" --type A --parent 기후에너지환경부 --filename "{name} 로고" \
    중앙환경분쟁조정피해구제위원회 전기위원회 국립야생동물질병관리원 온실가스종합정보센터 \
    낙동강홍수통제소 영산강홍수통제소 금강홍수통제소 한강홍수통제소 수도권대기환경청 \
    대구지방환경청 전북지방환경청 원주지방환경청 낙동강유역환경청 영산강유역환경청 \
    금강유역환경청 한강유역환경청
"${B[@]}" --out "$O" --type A --parent 기후에너지환경부 --filename "{name}" 화학물질안전원
"${B[@]}" --out "$O" --type A --parent 국토교통부 --filename "{name} 로고" 항공교통본부 중앙토지수용위원회 국토교통인재개발원
"${B[@]}" --out "$O" --type A --parent 고용노동부 --filename "{parent}{name} 로고" 고객상담센터
"${B[@]}" --out "$O" --type A --parent 식품의약품안전처 --filename "{name} 로고" 식품의약품안전평가원
"${B[@]}" --out "$O" --type A --parent 행정안전부 --filename "{name} 로고" 주민등록번호변경위원회 대통령기록관
"${B[@]}" --out "$O" --type A --parent 해양수산부 --filename "{name} 로고" 국립수산물품질관리원
"${B[@]}" --out "$O" --type A --parent 산림청 --filename "{name} 로고" \
    중부지방산림청 서부지방산림청 남부지방산림청 동부지방산림청 북부지방산림청 국립산림품종관리센터 산림교육원
"${B[@]}" --out "$O" --type A --parent 국가보훈부 --filename "{name} 로고" 보훈심사위원회
"${B[@]}" --out "$O" --type 국영B --filename "{name} 로고" \
    "국세공무원교육원=National Tax Officials Training Institute" \
    "관세평가분류원=Customs Valuation & Classification Institute" \
    "중앙관세분석소=Central Customs Laboratory And Scientific Service" \
    "국세상담센터=National Tax Consultation Center" "대테러센터=National Counter Terrorism Center"
"${B[@]}" --out "$O" --type 국영B --filename "국세청 주류면허지원센터 로고" "국세청주류면허지원센터=NTS Liquor License Support Center"
"${B[@]}" --out "$O" --type 국영B --filename "{name} 로고" \
    "국립4·19민주묘지=April 19th National Cemetery::국립4.19민주묘지" \
    "국립3·15민주묘지=March 15th National Cemetery::국립3.15민주묘지"
"${B[@]}" --out "$O" --type 국영A --filename "{name} 로고" "국가기후위기대응위원회=Presidential Commission|on Climate Crisis Response"
# 가이드에 없는 요청: 국문 양끝을 영문 폭에 맞춤
"${B[@]}" --out "$O" --type 국영B --justify --filename "{name} 로고" "무역위원회=KOREA TRADE COMMISSION"

python3 - "$O" <<'PY'
import glob, os, sys
from PIL import Image
O = sys.argv[1]
KEEP = {"조세심판원", "공무원재해보상연금위원회", "국가바이오혁신위원회", "산업재해보상보험재심사위원회",
        "국립김해박물관", "중앙환경분쟁조정피해구제위원회", "중부지방산림청", "국세공무원교육원",
        "국세청주류면허지원센터", "국립4.19민주묘지", "국가기후위기대응위원회"}
for f in glob.glob(f"{O}/구성규정_*.png"):
    if os.path.basename(f)[5:-4] not in KEEP:
        os.remove(f)
# 미리보기: 2열 격자 (가나다순)
files = sorted(glob.glob(f"{O}/png/*.png"))
H, gap, cols = 200, 16, 2
ims = [Image.open(f).convert("RGB") for f in files]
ims = [im.resize((round(im.width * H / im.height), H), Image.LANCZOS) for im in ims]
rows, cw = (len(ims) + cols - 1) // cols, max(im.width for im in ims)
sheet = Image.new("RGB", (cols * cw + (cols + 1) * gap, rows * H + (rows + 1) * gap), (232, 232, 232))
for k, im in enumerate(ims):
    r, c = divmod(k, cols)
    x, y = gap + c * (cw + gap), gap + r * (H + gap)
    sheet.paste(Image.new("RGB", (cw, H), "white"), (x, y))
    sheet.paste(im, (x, y))
sheet.save(f"{O}/미리보기.png")
print(f"{O}: {len(files)} 기관, 미리보기 {sheet.size}")
PY
