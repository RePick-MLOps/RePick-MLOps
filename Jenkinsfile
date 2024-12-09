pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.11'
        AWS_REGION = 'ap-northeast-3'
        DOCKER_IMAGE = 'jeonghyeran/rp-chat-bot'
        OPENAI_API_KEY = credentials('openai-api-key')
    }
    
    parameters {
        choice(
            name: 'UPDATE_TYPE',
            choices: ['all','crawling-only', 'pdf-only', 'docker-only', 'ec2-only'],
            description: '업데이트 유형을 선택하세요'
        )
    }

    triggers {
        cron('0 22 * * *')
    }

    stages {
        stage('Setup Chrome') {
            steps {
                sh '''
                    echo "=== Installing Chrome and dependencies ==="
                    
                    # snap 제거
                    sudo snap remove chromium || true
                    
                    # 기존 Chrome 관련 패키지 제거
                    sudo apt-get remove -y chromium-browser chromium-chromedriver
                    sudo apt-get autoremove -y
                    
                    # 특정 버전 설치
                    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
                    sudo apt-get install -y ./google-chrome-stable_current_amd64.deb
                    
                    # Chrome 버전 확인
                    CHROME_VERSION=$(google-chrome --version | cut -d " " -f3)
                    echo "Chrome version: $CHROME_VERSION"
                    
                    # ChromeDriver 설치
                    CHROMEDRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE)
                    wget -N https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip
                    unzip -o chromedriver_linux64.zip
                    sudo mv -f chromedriver /usr/local/bin/chromedriver
                    sudo chmod +x /usr/local/bin/chromedriver
                    
                    # Xvfb 설치 및 설정
                    sudo apt-get install -y xvfb
                    export DISPLAY=:99
                    Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &
                    
                    # 권한 설정
                    sudo chmod -R 777 /var/lib/jenkins/.wdm/
                    sudo chown -R jenkins:jenkins /var/lib/jenkins/.wdm/
                    
                    # 버전 확인
                    google-chrome --version
                    chromedriver --version
                '''
            }
        }

        stage('Daily Crawling') {
            when {
                anyOf {
                    allOf {
                        triggeredBy 'TimerTrigger'
                        expression { Calendar.getInstance().get(Calendar.HOUR_OF_DAY) == 22 }
                    }
                    expression {
                        return params.UPDATE_TYPE in ['all', 'crawling-only']
                    }
                }
            }
            steps {
                withCredentials([
                    string(credentialsId: 'ec2-host', variable: 'EC2_HOST'),
                    string(credentialsId: 'ec2-port', variable: 'EC2_PORT'),
                    string(credentialsId: 'db-user', variable: 'DB_USER'),
                    string(credentialsId: 'db-password', variable: 'DB_PASSWORD')
                ]) {
                    sh '''
                        export DISPLAY=:99
                        export PYTHONPATH="${WORKSPACE}"

                        echo "=== Starting Daily Crawling ==="
                        export PYTHONPATH="${WORKSPACE}"
                        
                        # Chromium 브라우저 설치
                        sudo apt-get update && sudo apt-get install -y chromium-browser
                        
                        # 크롤링 실행
                        python3 -m src.data_collection.crawling
                        
                        echo "=== Crawling Completed ==="

                    '''
                }
            }
        }

        stage('System Cleanup') {
            steps {
                sh '''
                    # 시스템 캐시 정리
                    sync
                    
                    # Jenkins 작업 디렉토리 정리
                    rm -rf ${WORKSPACE}/*
                    
                    echo "=== Docker Cleanup ==="
                    
                    # 컨테이너 정리
                    CONTAINERS=$(docker container ls -aq)
                    if [ ! -z "$CONTAINERS" ]; then
                        docker container stop $CONTAINERS
                        docker container rm $CONTAINERS
                    fi
                    
                    # 볼륨 정리
                    VOLUMES=$(docker volume ls -q)
                    if [ ! -z "$VOLUMES" ]; then
                        docker volume rm $VOLUMES
                    fi
                    
                    # Docker 빌드 캐시 완전 정리
                    docker builder prune -f --all
                    docker system prune -af --volumes
                    
                    # buildx 관련 모든 리소스 정리
                    echo "=== Buildx Cleanup ==="
                    # 현재 buildx 상태 확인
                    docker buildx ls
                    
                    # default 빌더를 제외한 모든 빌더 이름 추출 및 제거
                    docker buildx ls | while read line; do
                        if echo "$line" | grep -v "default" | grep -v "NAME" | grep -q "docker"; then
                            builder=$(echo "$line" | awk '{print $1}' | sed "s/*$//")
                            if [ ! -z "$builder" ]; then
                                echo "Removing builder: $builder"
                                docker buildx rm -f "$builder" || true
                            fi
                        fi
                    done
                    
                    # buildx 캐시 정리
                    docker buildx prune -f --all || true
                    
                    # buildx 상태 파일 직접 정리
                    rm -rf /var/lib/buildkit/runc-overlayfs/snapshots/* || true
                    rm -rf /var/lib/docker/buildx/* || true
                    
                    # 새로운 buildx 빌더 생성
                    echo "=== Creating new buildx builder ==="
                    docker buildx create --use --name fresh-builder
                    docker buildx inspect
                    
                    # 시스템 상태 확인
                    echo "=== System Status ==="
                    df -h
                    free -h
                    docker system df
                '''
            }
        }
        
        stage('Clean Docker') {
            steps {
                sh '''
                    # 모든 중지된 컨테이너 제거
                    docker container prune -f
                    
                    # 사용하지 않는 이미지 제거
                    docker image prune -a -f
                    
                    # 빌드 캐시 제거
                    docker builder prune -f --all
                    
                    # Docker 시스템 정리
                    docker system prune -af --volumes
                    
                    # 시스템 상태 확인
                    df -h
                '''
            }
        }
        
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Setup Python') {
            steps {
                script {
                    sh '/usr/bin/python3 --version'
                }
            }
        }
        
        stage('Configure AWS') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'aws-credentials',
                        usernameVariable: 'AWS_ACCESS_KEY_ID',
                        passwordVariable: 'AWS_SECRET_ACCESS_KEY'
                    )
                ]) {
                    sh """
                        aws configure set aws_access_key_id ${AWS_ACCESS_KEY_ID}
                        aws configure set aws_secret_access_key ${AWS_SECRET_ACCESS_KEY}
                        aws configure set region ${AWS_REGION}
                    """
                }
            }
        }
        
        stage('Install Dependencies') {
            steps {
                sh '''
                    apt-get update && apt-get install -y \
                        curl \
                        unzip \
                        tar \
                        build-essential \
                        g++ \
                        && curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
                        && unzip awscliv2.zip \
                        && ./aws/install \
                        && rm -rf aws awscliv2.zip \
                        && apt-get clean \
                        && rm -rf /var/lib/apt/lists/*
                    
                    /usr/bin/python3 -m pip install --upgrade pip
                    /usr/bin/python3 -m pip install --no-cache-dir pyOpenSSL==23.2.0
                    /usr/bin/python3 -m pip install --no-cache-dir -r requirements.txt
                '''
            }
        }
        
        stage('Setup Environment') {
            steps {
                withCredentials([
                    string(credentialsId: 'openai-api-key', variable: 'OPENAI_API_KEY'),
                    string(credentialsId: 'mongo-uri', variable: 'MONGO_URI'),
                    string(credentialsId: 'upstage-api-key', variable: 'UPSTAGE_API_KEY'),
                    string(credentialsId: 'aws-s3-bucket', variable: 'AWS_S3_BUCKET'),
                    string(credentialsId: 'ec2-host', variable: 'EC2_HOST'),
                    string(credentialsId: 'ec2-port', variable: 'EC2_PORT'),
                    string(credentialsId: 'db-user', variable: 'DB_USER'),
                    string(credentialsId: 'db-password', variable: 'DB_PASSWORD')
                ]) {
                    sh '''
                        echo "Checking MongoDB environment variables:"
                        echo "EC2_HOST: $EC2_HOST"
                        echo "EC2_PORT: $EC2_PORT"
                        echo "DB_USER: $DB_USER"
                        
                        mkdir -p data/pdf
                        mkdir -p data/vectordb
                        mkdir -p data/logs
                    '''
                }
            }
        }
        
        stage('Setup Directories') {
            steps {
                sh '''
                    # 필요한 디렉토리 한 번에 생성
                    mkdir -p data/pdf data/vectordb
                    
                    echo "=== 디렉토리 구조 확인 ==="
                    ls -la data/
                '''
            }
        }
        
        stage('Download Existing VectorDB') {
            steps {
                sh '''
                    echo "=== S3에서 VectorDB 다운로드 시작 ==="
                    
                    # 디렉토리 존재 확인 및 생성
                    mkdir -p data/vectordb
                    
                    # S3 버킷 내용물 확인
                    echo "=== S3 버킷 내용 확인 ==="
                    aws s3 ls s3://repick-chromadb/vectordb/ --recursive
                    
                    # 파일 다운로드
                    echo "=== VectorDB 파일 다운로드 ==="
                    aws s3 sync s3://repick-chromadb/vectordb/ data/vectordb/ \
                        --exclude "*" \
                        --include "*.sqlite3" \
                        --include "*.json" \
                        --include "*.bin" \
                        --include "*.pkl" \
                        --include "index/*"
                    
                    # 다운로드 결과 확인
                    echo "=== 다운로드된 파일 확인 ==="
                    ls -la data/vectordb/
                    
                    if [ ! -f "data/vectordb/chroma.sqlite3" ]; then
                        echo "경고: chroma.sqlite3 파일이 없습니다!"
                        exit 1
                    fi
                '''
            }
        }
        
        stage('Download PDFs') {
            when {
                expression { 
                    return params.UPDATE_TYPE in ['all', 'pdf-only'] 
                }
            }
            steps {
                withCredentials([
                    string(credentialsId: 'ec2-host', variable: 'EC2_HOST'),
                    string(credentialsId: 'ec2-port', variable: 'EC2_PORT'),
                    string(credentialsId: 'db-user', variable: 'DB_USER'),
                    string(credentialsId: 'db-password', variable: 'DB_PASSWORD')
                ]) {
                    sh '''
                        export PYTHONPATH="${PYTHONPATH}:$(pwd)"
                        echo "Running with environment:"
                        echo "EC2_HOST=$EC2_HOST"
                        echo "EC2_PORT=$EC2_PORT"
                        echo "DB_USER=$DB_USER"
                        /usr/bin/python3 src/utils/mongodb_utils.py
                    '''
                }
            }
        }
        
        stage('Process PDFs') {
            when {
                expression { 
                    return params.UPDATE_TYPE in ['all', 'pdf-only']
                }
            }
            steps {
                withCredentials([
                    string(credentialsId: 'upstage-api-key', variable: 'UPSTAGE_API_KEY')
                ]) {
                    sh '''
                        # PDF 처리 전 ChromaDB 상태 확인
                        echo "=== PDF 처리 전 ChromaDB 상태 ==="
                        ls -lh data/vectordb/chroma.sqlite3
                        md5sum data/vectordb/chroma.sqlite3
                        
                        # ChromaDB 컬렉션 상태 확인
                        echo "=== ChromaDB 처리 전 상태 확인 ==="
                        python3 -c "import chromadb; client = chromadb.PersistentClient(path='data/vectordb'); collection = client.get_collection('pdf_collection'); print(f'현재 문서 수: {collection.count()}')"
                        
                        # PDF 처리 및 ChromaDB 업데이트
                        echo "UPSTAGE_API_KEY: $UPSTAGE_API_KEY"
                        python3 scripts/process_pdfs.py --append_mode
                        
                        # PDF 처리 후 ChromaDB 상태 확인
                        echo "=== PDF 처리 후 ChromaDB 상태 ==="
                        ls -lh data/vectordb/chroma.sqlite3
                        md5sum data/vectordb/chroma.sqlite3
                        
                        # ChromaDB 컬렉션 상태 재확인
                        echo "=== ChromaDB 처리 후 상태 확인 ==="
                        python3 -c "import chromadb; client = chromadb.PersistentClient(path='data/vectordb'); collection = client.get_collection('pdf_collection'); print(f'처리 후 문서 수: {collection.count()}')"
                        
                        # 상태 확인
                        if [ -f "data/vectordb/processed_states.json" ]; then
                            echo "처리된 PDF 상태:"
                            cat data/vectordb/processed_states.json
                        fi
                    '''
                }
            }
        }
        
        stage('Upload to S3') {
            when {
                expression { 
                    return params.UPDATE_TYPE in ['all', 'pdf-only']
                }
            }
            steps {
                withCredentials([
                    string(credentialsId: 'aws-s3-bucket', variable: 'AWS_S3_BUCKET')
                ]) {
                    sh '''
                        echo "=== S3 업로드 시작 ==="
                        
                        # ChromaDB 디렉토리 내용 확인
                        echo "vectordb 디렉토리 내용:"
                        ls -la data/vectordb/
                        
                        # ChromaDB 파일들이 모두 업로드되도록 명시적으로 지정
                        aws s3 sync data/vectordb/ s3://repick-chromadb/vectordb/ \
                            --include "*.sqlite3" \
                            --include "*.json" \
                            --include "*.bin" \
                            --include "*.pkl" \
                            --include "index/*" \
                            --exclude "*" \
                            --size-only
                        
                        # 업로드 확인
                        echo "=== S3 업로드된 파일 목록 ==="
                        aws s3 ls s3://repick-chromadb/vectordb/ --recursive
                        
                        echo "S3 업로드 완료"
                    '''
                }
            }
        }
        
        stage('Build and Push Docker') {
            when {
                expression { 
                    return params.UPDATE_TYPE in ['all', 'docker-only']
                }
            }
            steps {
                script {
                    withCredentials([
                        usernamePassword(
                            credentialsId: 'docker-hub-credentials',
                            usernameVariable: 'DOCKER_USERNAME',
                            passwordVariable: 'DOCKER_PASSWORD'
                        )
                    ]) {
                        sh '''
                            echo $DOCKER_PASSWORD | docker login -u $DOCKER_USERNAME --password-stdin
                            
                            # Docker 이미지 빌드 및 푸시
                            docker build -t ${DOCKER_IMAGE}:latest .
                            docker push ${DOCKER_IMAGE}:latest
                            
                            # 빌드 완료 확인
                            echo "Docker 이미지가 성공적으로 빌드되어 Docker Hub에 푸시되었습니다."
                            echo "이미지: ${DOCKER_IMAGE}:latest"
                        '''
                    }
                }
            }
        }
        
        stage('Check AWS Configuration') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'aws-credentials',
                        usernameVariable: 'AWS_ACCESS_KEY_ID',
                        passwordVariable: 'AWS_SECRET_ACCESS_KEY'
                    )
                ]) {
                    sh '''
                        echo "=== AWS 설정 확인 ==="
                        aws --version
                        aws configure list
                        aws sts get-caller-identity
                    '''
                }
            }
        }
        
        stage('Setup Python Environment') {
            steps {
                sh '''
                    python3 -m pip install --upgrade pip
                    pip3 install -r requirements.txt
                '''
            }
        }
    }
    
    post {
        always {
            cleanWs() // 작업 공간 정리
            script {
                try {
                    slackSend( // Slack 알림
                        channel: '#jenkins', 
                        color: currentBuild.currentResult == 'SUCCESS' ? 'good' : 'danger',
                        message: """
                            *${currentBuild.currentResult}:* Job `${env.JOB_NAME}` build `${env.BUILD_NUMBER}`
                            More info at: ${env.BUILD_URL}
                        """,
                        tokenCredentialId: 'slack-token'
                    )
                } catch (Exception e) {
                    echo "Slack 알림 전송 실패: ${e.message}"
                }
            }
        }
        success {
            slackSend (
                channel: '#jenkins',
                color: 'good',
                message: """
                    :white_check_mark: 파이프라인 실행 성공
                    - 작업: ${env.JOB_NAME}
                    - 빌드 번호: ${env.BUILD_NUMBER}
                    - 상세 정보: ${env.BUILD_URL}
                """
            )
        }
        failure {
            slackSend (
                channel: '#jenkins',
                color: 'danger',
                message: """
                    :x: 파이프라인 실행 실패
                    - 작업: ${env.JOB_NAME}
                    - 빌드 번호: ${env.BUILD_NUMBER}
                    - 상세 정보: ${env.BUILD_URL}
                """
            )
        }
    }
} 