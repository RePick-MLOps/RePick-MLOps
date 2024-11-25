from google.colab import drive
drive.mount('/content/drive')

FILE_PATH = "/content/drive/MyDrive/한경_토스뱅크_2024/01_Machine Learning/05_추천시스템/data/tmdb_5000_movies.csv"

import pandas as pd

# 표시되는 컬럼의 가로 길이 키우기
pd.set_option("max_colwidth", 200)
movies = pd.read_csv(FILE_PATH)
movies.head()

"""# 필요한 Feature만 선택
- 장르와 키워드만을 이용해 콘텐츠 기반 필터링 수행
- 물론 장르 말고도 활용할 수 있는 기반 데이터는 많다
"""

movies_df = movies[["id", "title", "genres", "vote_average", "vote_count", "popularity", "keywords", "overview"]]
movies_df.info()

movies_df[['genres', 'keywords']].head()

"""실제 보이는 형식은 JSON 형식이지만, 실제로는 문자열 형태로 저장되어 있음!

- `json` 패키지를 이용해서 실제 json 객체 형식으로 바꿔줌
"""

import json

movies_df['genres'] = movies_df['genres'].apply(json.loads) # loads : 문자열로 되어 있는 json 형식의 문자열을 실제 json타입의 객체로 바꿔준다.
movies_df['keywords'] = movies_df['keywords'].apply(json.loads)

"""JSON : JavaScript Object Notation (자바스크립트 객체 **표현** 방식)

'''{"key": "value"}'''
"""

sample = [{'id': 28, 'name': 'Action'},
          {'id': 12, 'name': 'Adventure'},
          {'id': 14, 'name': 'Fantasy'},
          {'id': 878, 'name': 'Science Fiction'}]

[ data['name'] for data in sample ]

movies_df['genres'] = movies_df['genres'].apply(lambda datas : [ data['name'] for data in datas ])
movies_df['keywords'] = movies_df['keywords'].apply(lambda datas : [ data['name'] for data in datas ])

movies_df[['genres', 'keywords']].head()

"""# Feature Vectorization"""

# 장르 콘텐츠 필터링을 활용한 영화 추천 구현을 위해 장르 문자열을 Count Vector로 만듦
from sklearn.feature_extraction.text import CountVectorizer

# CountVectorer를 적용하기 위해 공백 문자로 word 단위가 구분되는 문자열로 변환
movies_df['genres_literal'] = movies_df['genres'].apply(lambda x : ' '.join(x))
movies_df[['genres', 'genres_literal']].head()

count_vect = CountVectorizer(ngram_range=(1, 2))
genre_matrix = count_vect.fit_transform(movies_df['genres_literal'])
genre_matrix

genre_matrix.toarray()

"""# 코사인 유사도
장르에 따른 영화 별 코사인 유사도 추출
"""

from sklearn.metrics.pairwise import cosine_similarity

genre_sim = cosine_similarity(genre_matrix, genre_matrix)
genre_sim.shape

# 첫 번째 영화(Avatar)에 대한 유사도 확인
genre_sim[0, :5]

"""각 영화마다 코사인 유사도가 가장 높은 영화를 구하기 위해 정렬"""

genre_sim_sorted_index = genre_sim.argsort()[:, ::-1]
genre_sim_sorted_index[0, :10]

# 함수의 목적 : 데이터 프레임에서 영화 제목을 받아, 그 영화와 가장 비슷한 top 10을 추출
def find_sim_movie(df, sorted_index, title_name, top_n=10):
  # 1. title_name 데이터 찾기
  title_movie = df[df['title'] == title_name]

  # 2. 찾고자 하는 영화의 인덱스 찾기
  title_index = title_movie.index.values
  similar_indexes = sorted_index[title_index, :top_n]

  similar_indexes = similar_indexes.reshape(-1) # 1차원 배열로 만들어 주기

  return df.iloc[similar_indexes]

similar_movies_df = find_sim_movie(movies_df, genre_sim_sorted_index, "The Godfather")
similar_movies_df[['title', 'vote_average', 'genres', 'keywords']]

"""숙제 : 장르, 키워드 기반의 콘텐츠 기반 필터링 추천 시스템 만들기

# 평점이 높은 순으로 추천
"""

movies_df[['title', 'vote_average', 'vote_count']].sort_values('vote_average', ascending=False).head(10)

"""## 평점 가중치 부여하기
투표 횟수가 적어도 vote_average가 높다면 평점이 높은 영화로 판단 될 수 있기 때문에 vote_count가 높은 상태에서도 높은 평점을 유지 하는 것이 정상적으로 평점이 높다고 할 수 있는 영화일 것이다.

새로운 가중평점은 다음과 같이 계산한다.
$$
가중평점(\text{Weighted Rating}) = R \times \frac{v}{(v+m)} + C \times \frac{m}{(v+m)}
$$
각 변수의 의미는 다음과 같다.
$$
v:\text{개별 영화에 평점을 투표한 횟수}\;\;m: \text{평점을 부여하기 위한 최소 투표 횟수}
$$
$$
R:\text{개별 영화에 대한 평균 평점}\;\;C: \text{전체 영화에 대한 평균 평점}
$$

예를 들어 A라는 영화의 투표 횟수가 1000회($v=1000$), 전체 데이터 세트 중에서 상위 60%의 투표 횟수가 300회($m=300$)라면 개별 영화 평점이 8.5점($R=8.5$), 전체 영화 평점이 6점($C=6.0$)일 때 다음과 같이 계산된다.
$$
8.5 \times \frac{1000}{1000 + 300} + 6.0 \times \frac{300}{1000+300}=7.92
$$


만약 상위 60%의 투표 횟수가 20회라면 어떻게 될까? 다른 영화들 보다 A라는 영화가 훨씬 더 투표에 많이 참여했기 때문에 더 많은 가중치를 받아 평점이 올라가게 된다.
$$
8.5 \times \frac{1000}{1000 + 20} + 6.0 \times \frac{20}{1000+20}=8.45
$$
"""

# 전체 영화에 대한 평균 평점
C = movies_df['vote_average'].mean()

# 상위 60% 지점의 투표 횟수 구하기
m = movies_df['vote_count'].quantile(0.6)

C, m

def weighted_vote_average(record):

  # 개별 영화의 투표 횟수와 평점
  v = record['vote_count']
  R = record['vote_average']

  # 가중 평점 공식 적용
  return (R * (v / (v + m))) + (C * (m / (v + m)))

movies_df['weighted_vote'] = movies_df.apply(weighted_vote_average, axis=1)
movies_df.head()

movies_df[['title', 'vote_average','weighted_vote', 'vote_count']].sort_values('weighted_vote', ascending=False).head(10)

# 가중 평점 기준으로 유사도 찾기 함수 재정의
def find_sim_movie(df, sorted_index, title_name, top_n=10):
  title_movie = df[df['title'] == title_name]
  title_index = title_movie.index.values

  # top_n의 2배에 해당하는 장르 유사성이 높은 index 추출
  #   유사성은 높은데 가중평점이 낮은 경우도 있기 때문에 10개를 보여줄 때도 2배수를 임의로 선정
  similar_indexes = sorted_index[title_index, : top_n*2]
  similar_indexes = similar_indexes.reshape(-1)

  # 검색한 영와는 제외
  similar_indexes = similar_indexes[similar_indexes != title_index]

  # top_n의 2배에 해당하는 후보군에서 weighted_vote 높은 순으로 top_n개 추출
  return df.iloc[similar_indexes].sort_values('weighted_vote', ascending=False)[:top_n]

similar_movies = find_sim_movie(movies_df, genre_sim_sorted_index, "The Godfather")
similar_movies[['title', 'vote_average', 'weighted_vote']]

"""콘텐츠 기반 필터링은 일반적으로 상품의 개수가 많은데, 사용자가 많이 없는 경우 사용"""

