import gradio as gr
from filtering import load_user_data, recommend_similar_reports
import pandas as pd


class ReportRecommenderBot:
    def __init__(self):
        """챗봇 초기화 및 사용자 데이터 로드"""
        self.user_data = load_user_data("chain_model/data/user_data-100.json")
        self.current_user_id = None

    def get_user_preferences(self, user_id):
        """사용자 ID로 선호도 정보 조회"""
        try:
            user = self.user_data[self.user_data["userId"] == user_id].iloc[0]
            return user
        except IndexError:
            return None

    def chat(self, message, history):
        """챗봇 대화 처리"""
        # 사용자 ID 입력 확인
        if "내 아이디는" in message or "ID는" in message:
            user_id = message.split()[-1]
            user = self.get_user_preferences(user_id)

            if user is not None:
                self.current_user_id = user_id
                industries = ", ".join(user["preferredIndustries"])
                companies = ", ".join(user["preferredCompanies"])
                return f"환영합니다! 선호하시는 산업군은 {industries}이고, 관심 기업은 {companies}입니다. 어떤 리포트를 추천해드릴까요?"
            else:
                return "죄송합니다. 해당 사용자 ID를 찾을 수 없습니다."

        # 리포트 추천 요청
        if "추천" in message and self.current_user_id:
            user_preferences = self.get_user_preferences(self.current_user_id)
            recommended_reports = recommend_similar_reports(user_preferences)

            response = "다음 리포트들을 추천드립니다:\n"
            for i, report in enumerate(recommended_reports, 1):
                response += f"{i}. {report['title']}\n"
            return response

        # 기본 응답
        if not self.current_user_id:
            return "사용자 ID를 알려주세요. '내 아이디는 [ID]' 형식으로 입력해주세요."
        return "리포트 추천을 원하시면 '리포트 추천해줘'라고 말씀해주세요."


# Gradio 인터페이스 생성
def create_chatbot():
    bot = ReportRecommenderBot()

    interface = gr.ChatInterface(
        bot.chat,
        title="리포트 추천 챗봇",
        description="사용자 맞춤 리포트 추천 서비스입니다. 시작하려면 '내 아이디는 [ID]'를 입력해주세요.",
        theme="soft",
    )

    return interface


if __name__ == "__main__":
    chatbot = create_chatbot()
    chatbot.launch()
