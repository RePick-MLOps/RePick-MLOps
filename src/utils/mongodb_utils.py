from pymongo import MongoClient
import gridfs
import os

# MongoDB에 연결
client = MongoClient('mongodb://localhost:27017/')
db = client['pdf_database']  # 데이터베이스 선택
fs = gridfs.GridFS(db)  # GridFS 객체 생성

def store_pdf(file_path):
    """
    PDF 파일을 MongoDB에 저장하는 함수

    :param file_path: 저장할 PDF 파일의 경로
    """
    if not os.path.exists(file_path):
        print(f"파일이 존재하지 않습니다: {file_path}")
        return

    with open(file_path, 'rb') as f:
        file_data = f.read()
        # 파일 이름을 사용하여 GridFS에 파일 저장
        fs.put(file_data, filename=os.path.basename(file_path))
    print(f"{file_path} 저장 완료")

def retrieve_pdf(file_name, output_path):
    """
    MongoDB에서 PDF 파일을 가져오는 함수

    :param file_name: 가져올 PDF 파일의 이름
    :param output_path: 저장할 경로
    """
    # 파일 이름으로 GridFS에서 파일 검색
    file_data = fs.find_one({'filename': file_name})
    if file_data:
        with open(output_path, 'wb') as f:
            f.write(file_data.read())
        print(f"{file_name} 가져오기 완료")
    else:
        print(f"{file_name}을(를) 찾을 수 없습니다.")

# 예제 사용
store_pdf('data/pdf/sample.pdf')  # PDF 파일 저장
retrieve_pdf('sample.pdf', 'data/pdf/retrieved_sample.pdf')  # PDF 파일 가져오기