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
- YouTube 피드는 요청마다 무작위로 404/500을 낸다 (2026-10-10 GitHub 러너 실측 약 65% 실패, 로컬 약 10%) → `fetch`가 GET을 최대 12회 시도한다.
- 예약 방송은 "방송 예정"으로 예약 시점에 한 번만 알린다(시작 시점 재알림 없음).

## FILE MAP
- `check.py` — 피드 확인 + Discord 전송
- `test_check.py` — 피드 파싱 자체 점검 (`python3 test_check.py`)
- `seen.json` — 이미 알린 영상 ID
- `.github/workflows/notify.yml` — 5분 주기 실행

## RULES
- 웹후크 주소는 코드/커밋에 넣지 않는다. GitHub Secret만 사용.
