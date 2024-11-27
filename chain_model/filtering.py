import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics.pairwise import cosine_similarity

def load_user_data(json_path):
    """사용자 데이터를 로드하고 전처리하는 함수"""
    user_data = pd.read_json(json_path)
    
    # 필요한 컬럼만 선택
    user_data = user_data[['userId', 'gender', 'age', 'reports', 
                           'preferredIndustries', 'preferredCompanies', 'bookmark', 'downLoad', 'recentReports']]

    return user_data

def create_report_features(pdf_dir):
    """PDF 문서들의 특징을 추출하는 함수"""
    # PDF 문서들의 메타데이터 로드 (industry, company 등)
    # 실제 구현시에는 PDF에서 메타데이터를 추출하는 로직 필요
    report_data = pd.DataFrame({
        'report_id': [],
        'industry': [],
        'company': []
    })

# 산업군과 종목에 대한 이진 인코딩
mlb_industry = MultiLabelBinarizer()
mlb_stock = MultiLabelBinarizer()

user_industry_encoded = mlb_industry.fit_transform(user_data['preferred_industries'])
user_stock_encoded = mlb_stock.fit_transform(user_data['preferred_stocks'])

# 사용자 데이터에 인코딩된 특징 추가
user_features = pd.concat([
    user_data[['user_id', 'gender', 'age']],
    pd.DataFrame(user_industry_encoded, columns=mlb_industry.classes_),
    pd.DataFrame(user_stock_encoded, columns=mlb_stock.classes_)
], axis=1)

from sklearn.metrics.pairwise import cosine_similarity

# 리포트 데이터에 대한 이진 인코딩
report_industry_encoded = mlb_industry.transform(report_data['industry'].apply(lambda x: [x]))
report_stock_encoded = mlb_stock.transform(report_data['stock'].apply(lambda x: [x]))

# 사용자 데이터에 인코딩된 특징 추가
user_features = pd.concat([
    user_data[['user_id', 'gender', 'age']],
    pd.DataFrame(user_industry_encoded, columns=mlb_industry.classes_),
    pd.DataFrame(user_stock_encoded, columns=mlb_stock.classes_)
], axis=1).fillna(0)  # NaN 값을 0으로 대체

# 리포트 데이터에 인코딩된 특징 추가
report_features = pd.concat([
    report_data[['report_id']],
    pd.DataFrame(report_industry_encoded, columns=mlb_industry.classes_),
    pd.DataFrame(report_stock_encoded, columns=mlb_stock.classes_)
], axis=1).fillna(0)  # NaN 값을 0으로 대체

from src.vectorstore import VectorStore

def recommend_similar_reports(user_preferences: str, top_k: int = 5):
    """사용자 선호도를 바탕으로 유사한 리포트 추천"""
    
    # 벡터스토어 초기화
    vector_store = VectorStore(persist_directory="./data/vectordb")
    
    # 사용자 선호도를 쿼리로 사용하여 유사한 문서 검색
    # 예: 선호 산업군과 기업을 문자열로 변환
    query = f"{' '.join(user_preferences['preferredIndustries'])} {' '.join(user_preferences['preferredCompanies'])}"
    
    similar_docs = vector_store.similarity_search(
        query=query,
        k=top_k,
        collection_name="pdf_collection"
    )
    
    return similar_docs

recommended_reports = recommend_similar_reports(user_preferences)

# 사용자와 리포트 간의 유사도 계산
user_report_similarity = cosine_similarity(user_features.drop(['user_id', 'gender', 'age'], axis=1), report_features.drop('report_id', axis=1))

# 추천 결과 생성
def recommend_reports(user_id, top_n=5):
    user_idx = user_data[user_data['user_id'] == user_id].index[0]
    similar_reports_idx = user_report_similarity[user_idx].argsort()[-top_n:][::-1]
    return report_data.iloc[similar_reports_idx]['report_id'].tolist()

# 예시: 사용자 1에게 추천할 리포트
recommended_reports = recommend_reports(user_id=1)
print(recommended_reports)

# 사용 예시
user_id = "1"
user_data = load_user_data("chain_model/data/user_data-100.json")
user_preferences = user_data[user_data['userId'] == user_id].iloc[0]