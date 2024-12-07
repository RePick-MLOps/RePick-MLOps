from pymongo import MongoClient
import logging
from collections import Counter
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# MongoDB 연결 정보
MONGO_URI = f"mongodb://admin:1111@{os.getenv('EC2_HOST')}:{os.getenv('EC2_PORT')}/research_db?authSource=admin"


def recommend_similar_reports(user_preferences):
    """사용자 선호도를 기반으로 리포트를 추천하는 함수"""
    try:
        # 사용자 선호도 요소 추출
        preferred_industries = set(user_preferences.get("preferredIndustries", []))
        preferred_companies = set(user_preferences.get("preferredCompanies", []))
        bookmarks = set(user_preferences.get("bookmark", []))
        downloads = set(user_preferences.get("downLoad", []))
        recent_reports = set(user_preferences.get("recentReports", []))

        print("\n추천 시스템 디버깅 정보:")
        print(f"선호 산업: {preferred_industries}")
        print(f"선호 기업: {preferred_companies}")
        print(f"북마크: {bookmarks}")
        print(f"다운로드: {downloads}")

        # MongoDB 연결
        client = MongoClient(MONGO_URI)
        db = client.research_db
        reports_collection = db.reports

        # 점수 기반 추천 시스템
        report_scores = {"Company": Counter(), "Industry": Counter()}

        # 1. 북마크한 리포트와 유사한 기업의 리포트 검색
        if bookmarks:
            for report_id in bookmarks:
                report = reports_collection.find_one({"report_id": int(report_id)})
                if report:
                    similar_reports = reports_collection.find(
                        {"company_name": {"$in": list(preferred_companies)}}
                    )
                    for similar in similar_reports:
                        report_type = similar.get(
                            "report_type", "Company"
                        )  # 기본값 Company
                        if similar["report_id"] not in bookmarks and report_type in [
                            "Company",
                            "Industry",
                        ]:
                            report_scores[report_type][similar["report_id"]] += 3

        # 2. 선호 기업의 최신 리포트
        if preferred_companies:
            company_reports = reports_collection.find(
                {"company_name": {"$in": list(preferred_companies)}}
            ).sort("report_date", -1)

            for report in company_reports:
                report_type = report.get("report_type", "Company")
                if report_type in ["Company", "Industry"]:
                    report_scores[report_type][report.get("report_id")] += 2

        # 3. 유사한 증권사의 리포트
        if bookmarks:
            for report_id in bookmarks:
                report = reports_collection.find_one({"report_id": int(report_id)})
                if report:
                    securities_firm = report.get("securities_firm")
                    if securities_firm:
                        similar_reports = reports_collection.find(
                            {"securities_firm": securities_firm}
                        ).sort("report_date", -1)

                        for similar in similar_reports:
                            report_type = similar.get("report_type", "Company")
                            if report_type in ["Company", "Industry"]:
                                report_scores[report_type][similar["report_id"]] += 1

        # Company와 Industry 각각 5개씩 선택
        recommendations = {
            "Company_recommendedReports": [],
            "Industry_recommendedReports": [],
        }

        for report_type in ["Company", "Industry"]:
            type_recommendations = [
                report_id
                for report_id, score in report_scores[report_type].most_common(5)
                if report_id not in bookmarks
                and report_id not in downloads
                and report_id not in recent_reports
            ]
            recommendations[f"{report_type}_recommendedReports"] = type_recommendations

        print(
            f"\nCompany 추천 수: {len(recommendations['Company_recommendedReports'])}"
        )
        print(
            f"Industry 추천 수: {len(recommendations['Industry_recommendedReports'])}"
        )

        return recommendations

    except Exception as e:
        print(f"추천 알고리즘 오류: {str(e)}")
        logging.error(f"추천 알고리즘 오류: {str(e)}")
        return {"Company_recommendedReports": [], "Industry_recommendedReports": []}
    finally:
        client.close()


def update_all_recommendations():
    try:
        # EC2 MongoDB 연결
        client = MongoClient(MONGO_URI)
        db = client.research_db
        user_collection = db.user
        reports_collection = db.reports

        # MongoDB 연결 확인
        print("\nMongoDB 연결 상태 확인...")
        print(f"Available databases: {client.list_database_names()}")
        print(f"Collections in research_db: {db.list_collection_names()}")

        # reports 컬렉션 확인
        reports_count = reports_collection.count_documents({})
        print(f"\nReports 컬렉션 문서 수: {reports_count}")
        if reports_count > 0:
            sample_report = reports_collection.find_one()
            print(f"Sample report: {sample_report}")

        # 처음 10명의 사용자만 조회
        all_users = list(user_collection.find().limit(10))

        updated_count = 0

        # 각 사용자별로 추천 생성 및 업데이트
        for user in all_users:
            try:
                user_id = user["userId"]

                user_preferences = {
                    "preferredIndustries": user.get("preferredIndustries", []),
                    "preferredCompanies": user.get("preferredCompanies", []),
                    "bookmark": user.get("bookmark", []),
                    "downLoad": user.get("downLoad", []),
                    "recentReports": user.get("recentReports", []),
                }

                print("선호도 정보 추출 완료")
                print(f"선호도 정보: {user_preferences}")

                # 추천 리포트 생성
                recommended_reports = recommend_similar_reports(user_preferences)
                print(
                    f"Company 추천 리포트: {len(recommended_reports['Company_recommendedReports'])} 개"
                )
                print(
                    f"Industry 추천 리포트: {len(recommended_reports['Industry_recommendedReports'])} 개"
                )

                if any(
                    recommended_reports.values()
                ):  # 추천 리포트가 있는 경우에만 업데이트
                    # MongoDB 문서 업데이트
                    result = user_collection.update_one(
                        {"userId": user_id},
                        {
                            "$set": {
                                "Company_recommendedReports": recommended_reports[
                                    "Company_recommendedReports"
                                ],
                                "Industry_recommendedReports": recommended_reports[
                                    "Industry_recommendedReports"
                                ],
                            }
                        },
                    )

                    print(
                        f"업데이트 결과: matched={result.matched_count}, modified={result.modified_count}"
                    )

                    if result.modified_count > 0:
                        updated_count += 1
                        print(f"사용자 {user_id}의 추천 업데이트 완료")
                else:
                    print(f"사용자 {user_id}에 대한 추천 리포트가 생성되지 않았습니다.")

            except Exception as e:
                print(f"사용자 {user_id} 처리 중 오류 발생: {str(e)}")
                continue

        print(
            f"\n총 {updated_count}/{len(all_users)} 명의 사용자 추천이 업데이트되었습니다."
        )

    except Exception as e:
        logging.error(f"추천 업데이트 중 오류 발생: {str(e)}")
        raise  # 에러를 표시하도록 수정
    finally:
        client.close()


if __name__ == "__main__":
    update_all_recommendations()
