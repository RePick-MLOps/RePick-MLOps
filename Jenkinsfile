pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.11'
        AWS_REGION = 'ap-northeast-3'
        DOCKER_IMAGE = 'jeonghyeran/rp-chat-bot'
    }
    
    parameters {
        choice(
            name: 'UPDATE_TYPE',
            choices: ['all', 'pdf-only', 'docker-only'],
            description: '업데이트 유형을 선택하세요'
        )
    }
    
    stages {
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
                        echo "UPSTAGE_API_KEY: $UPSTAGE_API_KEY"
                        /usr/bin/python3 scripts/process_pdfs.py
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
                    string(credentialsId: 'aws-s3-bucket', variable: 'AWS_S3_BUCKET'),
                    usernamePassword(
                        credentialsId: 'aws-credentials',
                        usernameVariable: 'AWS_ACCESS_KEY_ID',
                        passwordVariable: 'AWS_SECRET_ACCESS_KEY'
                    )
                ]) {
                    sh '''
                        echo "=== S3 업로드 디버깅 ==="
                        echo "AWS_S3_BUCKET: ${AWS_S3_BUCKET}"
                        
                        echo "=== ChromaDB 데이터 직접 업로드 시작 ==="
                        echo "=== vectordb 디렉토리 내용 ==="
                        ls -la data/vectordb/
                        
                        # ChromaDB 데이터 직접 동기화
                        aws s3 sync data/vectordb/ s3://${AWS_S3_BUCKET}/vectordb/ --delete
                        
                        echo "Upload completed"
                    '''
                }
            }
        }
        
        stage('Build and Push Docker') {
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
                            
                            # buildx 빌더 설정 확인
                            docker buildx inspect
                            
                            # 빌드 시도 (캐시 사용하지 않음)
                            docker buildx build --no-cache \
                                --platform linux/amd64,linux/arm64 \
                                -t ${DOCKER_IMAGE}:v1.1 \
                                -t ${DOCKER_IMAGE}:latest \
                                --push .
                        '''
                    }
                }
            }
        }
        
        stage('Deploy to ECS') {
            when {
                expression { 
                    return params.UPDATE_TYPE in ['all', 'docker-only']
                }
            }
            steps {
                sh '''
                    aws ecs update-service \
                        --cluster repick-cluster \
                        --service repick-service \
                        --force-new-deployment
                '''
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
    }
    
    post {
        always {
            cleanWs()
        }
    }
} 