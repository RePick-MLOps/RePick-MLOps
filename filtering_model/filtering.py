from pymongo import MongoClient
import pandas as pd


def get_recommended_reports(user_id):
    """사용자 ID를 기반으로 추천 리포트를 반환하는 함수"""
    try:
        # MongoDB 연결
        client = MongoClient("mongodb://localhost:27017/")
        db = client.research_db
        collection = db.UsrRecRptDB

        # 사용자 정보 조회
        user = collection.find_one({"userId": user_id})
        if not user:
            return "사용자를 찾을 수 없습니다."

        # 사용자 선호도 정보를 pandas Series로 변환
        user_preferences = pd.Series(user)

        # 리포트 추천 로직 실행
        recommended_reports = recommend_similar_reports(user_preferences)

        return recommended_reports

    except Exception as e:
        return f"오류 발생: {str(e)}"
    finally:
        client.close()


if __name__ == "__main__":
    # 테스트용 예시
    user_id = "test_user_id"
    reports = get_recommended_reports(user_id)
    print(reports)
