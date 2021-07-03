# Discord Datamining Bot - Python
[ItsRauf/dataminev2](https://github.com/ItsRauf/dataminev2/)의 봇을 파이썬으로 제작한 버전입니다.

매 10분마다 [Discord-Datamining/Discord-Datamining](https://github.com/Discord-Datamining/Discord-Datamining)의 커밋을 체크해 구독된 채널에게 알림을 전송합니다.

## 사용
1. 직접 봇 호스팅
2. 미니봇을 이용
    - 봇 [초대](https://discordapp.com/oauth2/authorize?client_id=520830713696878592&scope=bot&permissions=8)하기
    - 원하는 채널에서 `미니봇 구독` 커맨드 입력
    - *"Let the magic happen!"*


## 실행
config.py에 봇 토큰과 깃허브 토큰 작성 후,
```bash
pip install -r requirements.txt

python bot.py
```

## 커맨드
`!구독` 커맨드를 사용한 채널에서 데이터마이닝 알림을 구독합니다. !!**`웹후크 관리하기` 권한이 필요합니다.**!!

`!구독 취소` 데이터마이닝 알림 구독을 취소합니다. !!**`웹후크 관리하기` 권한이 필요합니다.**!!

`!최신` 최신 데이터마이닝 댓글을 가져옵니다.

`!검색 [query]` DB에서 검색어를 검색합니다.

`!종료` DB를 정리 후, 프로세스를 종료합니다.