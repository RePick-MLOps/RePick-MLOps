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
                    [
                        $class: 'AmazonWebServicesCredentialsBinding',
                        credentialsId: 'aws-credentials',
                        accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                        secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                    ]
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
                    python -m pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }
        
        stage('Setup Environment') {
            steps {
                withCredentials([
                    string(credentialsId: 'openai-api-key', variable: 'OPENAI_API_KEY'),
                    string(credentialsId: 'mongo-uri', variable: 'MONGO_URI'),
                    string(credentialsId: 'upstage-api-key', variable: 'UPSTAGE_API_KEY'),
                    string(credentialsId: 'aws-s3-bucket', variable: 'AWS_S3_BUCKET')
                ]) {
                    sh '''
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
                sh '''
                    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
                    python src/utils/mongodb_utils.py
                '''
            }
        }
        
        stage('Process PDFs') {
            when {
                expression { 
                    return params.UPDATE_TYPE in ['all', 'pdf-only']
                }
            }
            steps {
                sh '''
                    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
                    python scripts/process_pdfs.py
                '''
            }
        }
        
        stage('Upload to S3') {
            when {
                expression { 
                    return params.UPDATE_TYPE in ['all', 'pdf-only']
                }
            }
            steps {
                sh '''
                    echo "Starting ChromaDB upload to S3..."
                    ls -la data/vectordb/
                    tar -czf vectordb.tar.gz -C data/vectordb .
                    echo "Created tar file:"
                    ls -lh vectordb.tar.gz
                    aws s3 cp vectordb.tar.gz s3://${AWS_S3_BUCKET}/vectordb/vectordb.tar.gz --debug
                    echo "Upload completed"
                '''
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
                    def version = env.TAG_NAME ? env.TAG_NAME : 'latest'
                    
                    withCredentials([
                        usernamePassword(
                            credentialsId: 'docker-hub-credentials',
                            usernameVariable: 'DOCKER_USERNAME',
                            passwordVariable: 'DOCKER_PASSWORD'
                        )
                    ]) {
                        sh """
                            docker login -u ${DOCKER_USERNAME} -p ${DOCKER_PASSWORD}
                            docker buildx create --use
                            docker buildx build --platform linux/amd64,linux/arm64 \
                                -t ${DOCKER_IMAGE}:v1.1 \
                                -t ${DOCKER_IMAGE}:latest \
                                --push .
                        """
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
    }
    
    post {
        always {
            cleanWs()
        }
    }
} 