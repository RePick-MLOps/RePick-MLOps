# scripts/run_pipeline.sh
#!/bin/bash

export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 1. PDF 처리
echo "Processing PDFs..."
python scripts/process_pdfs.py

# 2. 상태 확인
echo "Checking processed states..."
python scripts/check_states.py

# 3. API 서버 시작
echo "Starting API server..."
python app/main.py