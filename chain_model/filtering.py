import pandas as pd

# 사용자 데이터 예시
user_data = pd.DataFrame({
    'user_id': [1, 2, 3],
    'gender': ['M', 'F', 'M'],
    'age': [25, 30, 22],
    'viewed_reports': [['report1', 'report2'], ['report3'], ['report1', 'report4']],
    'preferred_industries': [['Tech', 'Finance'], ['Health'], ['Tech']],
    'preferred_stocks': [['AAPL', 'GOOGL'], [], ['TSLA', 'MSFT']],  # 'MSFT' 추가
    'bookmarked_reports': [['report1'], ['report3'], []],
    'downloaded_reports': [['report2'], [], ['report4']],
    'recent_reports': [['report1', 'report2'], ['report3'], ['report4']]
})

# 리포트 데이터 예시
report_data = pd.DataFrame({
    'report_id': ['report1', 'report2', 'report3', 'report4'],
    'industry': ['Tech', 'Finance', 'Health', 'Tech'],
    'stock': ['AAPL', 'GOOGL', 'TSLA', 'MSFT']
})

from sklearn.preprocessing import MultiLabelBinarizer

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