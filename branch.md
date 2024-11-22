# branch 사용법
* main에서 작업하지 않고 항상 작업할 branch로 이동 후 작업
    * git fetch --all : 변경사항 확인
    * git pull : 변경사항 가져오기
    * git checkout <브랜치명> : 브랜치 변경
* 변경사항 commit
    * git add . : 변경사항 전부 add
        * git add <파일명> : 추가하고 싶은 변경사항만 add
    * git commit -m "커밋 메시지"
        * \<Type>: \<description>
        * 이하 Type 구분
            * Feat : 새로운 기능
            * Fix : 버그 수정
            * Build : 빌드 관련 파일 수정
            * Style: 스타일 관련 기능(코드 포맷팅, 세미콜론 누락, 코드 자체의 변경이 없는 경우)
            * Chore : 빌드 업무 수정, 패키지 매니저 수정(ex .gitignore 수정)
            * Refactor: 코드 리팩토링
            * Test : 테스트 코드 추가 및 수정
            * Docs : 문서 수정
    * git push 또는 git push origin <브랜치명>
    * 깃허브에서 pull request