# STATUS.md

## BIG PROJECT GOAL
유튜버의 새 영상/방송을 Discord 웹후크로 알림 (GitHub Actions, 서버 없음).

## CURRENT CHRONOLOGICAL STEP
완료 — 운영 중.

## CURRENT VERIFIED STATE
- 저장소: https://github.com/jawvcl/youtube-discord-notify (공개)
- 5분마다 `.github/workflows/notify.yml`이 `check.py`를 실행한다.
- 2026-10-09 첫 실행에서 두 채널 최신 영상 1개씩 Discord 전송 성공, 재실행 시 중복 전송 없음.

## CURRENT BLOCKERS
- GitHub 예약 실행이 5분이 아니라 실제로는 3~7시간 간격으로만 돈다 (2026-10-08~10 관측: 30시간에 6회).

## NEXT ACTION
- 없음. 채널을 추가하려면: `check.py`의 `CHANNELS`에 채널 ID와 Secret 이름을 한 줄 추가하고,
  `gh secret set <이름>`으로 웹후크 주소를 저장한다.

## VERIFIED FACTS
- 팁7 채널 ID `UCJMW5nKtT9uSHWINC-aAUPw` → Secret `WEBHOOK_TIPP7`
- 죠브 채널 ID `UCEnjAAmVQ9wx8CDPDV6Y4sg` → Secret `WEBHOOK_JYOBU`
- `seen.json`은 Actions가 자동 커밋한다. 로컬에서 푸시하기 전에 `git pull --rebase` 필요.
- YouTube RSS 피드는 GitHub 러너에서 몇 분씩 통째로 404/500이 난다 (2026-10-10 실측: 러너 6대 중 2대가 4분 내내 실패, 재시도로 해결 안 됨). 업로드 재생목록 페이지(`playlist?list=UU…`)는 같은 실측에서 24/24 성공 → 이것이 주 소스이고, RSS는 페이지를 못 읽을 때만 쓰는 예비다.
- 재생목록 상위 15개는 RSS 피드와 ID·제목·순서가 동일함을 확인했다 (2026-10-10).
- 새 영상 = 목록 맨 위부터 이미 알린 영상이 나오기 전까지. 한 번에 최대 5개.
- 예약 방송은 "방송 예정"으로 예약 시점에 한 번만 알린다(시작 시점 재알림 없음).

## FILE MAP
- `check.py` — 새 영상 확인 + Discord 전송
- `test_check.py` — 자체 점검 (`python3 test_check.py`)
- `seen.json` — 이미 알린 영상 ID
- `.github/workflows/notify.yml` — 5분 주기 실행

## RULES
- 웹후크 주소는 코드/커밋에 넣지 않는다. GitHub Secret만 사용.
