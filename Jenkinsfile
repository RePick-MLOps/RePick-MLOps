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
                    sync
                    rm -rf ${WORKSPACE}/*

                    echo "=== Docker Cleanup ==="
                    docker container stop $(docker container ls -aq) || true
                    docker container rm $(docker container ls -aq) || true
                    docker volume rm $(docker volume ls -q) || true
                    docker builder prune -f --all
                    docker system prune -af --volumes

                    echo "=== Buildx Cleanup ==="
                    docker buildx rm -f $(docker buildx ls | grep -v default | awk '{print $1}') || true
                    docker buildx prune -f --all
                    rm -rf /var/lib/buildkit/runc-overlayfs/snapshots/* /var/lib/docker/buildx/* || true

                    echo "=== Creating New Buildx Builder ==="
                    docker buildx create --use --name fresh-builder
                    docker buildx inspect

                    echo "=== System Status ==="
                    df -h
                    free -h
                    docker system df
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
                sh '/usr/bin/python3 --version'
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
                    sh '''
                        aws configure set aws_access_key_id ${AWS_ACCESS_KEY_ID}
                        aws configure set aws_secret_access_key ${AWS_SECRET_ACCESS_KEY}
                        aws configure set region ${AWS_REGION}
                    '''
                }
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    apt-get update && apt-get install -y \
                        curl unzip tar build-essential g++ \
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
                        echo "Checking Environment Variables"
                        mkdir -p data/pdf data/vectordb data/logs
                    '''
                }
            }
        }

        stage('Download and Process PDFs') {
            when {
                expression { params.UPDATE_TYPE in ['all', 'pdf-only'] }
            }
            steps {
                withCredentials([
                    string(credentialsId: 'upstage-api-key', variable: 'UPSTAGE_API_KEY'),
                    string(credentialsId: 'aws-s3-bucket', variable: 'AWS_S3_BUCKET')
                ]) {
                    sh '''
                        export PYTHONPATH="${PYTHONPATH}:$(pwd)"
                        /usr/bin/python3 src/utils/mongodb_utils.py
                        /usr/bin/python3 scripts/process_pdfs.py
                        aws s3 sync data/vectordb/ s3://${AWS_S3_BUCKET}/vectordb/ --delete
                    '''
                }
            }
        }

        stage('Build and Push Docker') {
            when {
                expression { params.UPDATE_TYPE in ['all', 'docker-only'] }
            }
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'docker-hub-credentials',
                        usernameVariable: 'DOCKER_USERNAME',
                        passwordVariable: 'DOCKER_PASSWORD'
                    )
                ]) {
                    sh '''
                        echo $DOCKER_PASSWORD | docker login -u $DOCKER_USERNAME --password-stdin
                        docker buildx build --no-cache \
                            --platform linux/amd64,linux/arm64 \
                            -t ${DOCKER_IMAGE}:v1.1 \
                            -t ${DOCKER_IMAGE}:latest \
                            --push .
                    '''
                }
            }
        }

        stage('Deploy to ECS') {
            when {
                expression { params.UPDATE_TYPE in ['all', 'docker-only'] }
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
