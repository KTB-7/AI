pipeline {
    agent any
    environment {
        AWS_REGION = 'ap-northeast-2'
        ECR_REPO = '528938155874.dkr.ecr.ap-northeast-2.amazonaws.com/pinpung/ecr'
        DOCKER_IMAGE_TAG = 'ai-latest' // AI 이미지 태그
        TARGET_EC2 = 'ec2-user@ip-10-0-8-96.ap-northeast-2.compute.internal'
    }
    stages {
        stage('Checkout Code') {
            steps {
                git branch: 'main', url: 'https://github.com/KTB-7/AI.git'
            }
        }
        stage('Build Docker Image') {
            steps {
                script {
                    sh """
                    docker build --memory=2g -t ${ECR_REPO}:${DOCKER_IMAGE_TAG} .
                    """
                }
            }
        }
        stage('Push to ECR') {
            steps {
                script {
                    sh """
                    aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REPO}
                    docker push ${ECR_REPO}:${DOCKER_IMAGE_TAG}
                    """
                }
            }
        }
        stage('Deploy to AI EC2') {
            steps {
                sshagent(['ec2-ssh-key']) {
                    script {
                        // 민감한 정보를 Jenkins 변수로 저장
                        def openaiApiKey = sh(script: "aws ssm get-parameter --name /pinpung/OPENAI_API_KEY --query Parameter.Value --output text --with-decryption --region ${AWS_REGION}", returnStdout: true).trim()
                        def mysqlHost = sh(script: "aws ssm get-parameter --name /pinpung/DB_HOST --query Parameter.Value --output text --region ${AWS_REGION}", returnStdout: true).trim()
                        def mysqlPort = sh(script: "aws ssm get-parameter --name /pinpung/DB_PORT --query Parameter.Value --output text --region ${AWS_REGION}", returnStdout: true).trim()
                        def mysqlUser = sh(script: "aws ssm get-parameter --name /pinpung/DB_AI_USERNAME --query Parameter.Value --output text --region ${AWS_REGION}", returnStdout: true).trim()
                        def mysqlPassword = sh(script: "aws ssm get-parameter --name /pinpung/DB_AI_PASSWORD --query Parameter.Value --output text --with-decryption --region ${AWS_REGION}", returnStdout: true).trim()
                        def mysqlDatabase = sh(script: "aws ssm get-parameter --name /pinpung/DB_NAME --query Parameter.Value --output text --region ${AWS_REGION}", returnStdout: true).trim()

                        // SSH를 통해 EC2에서 .env 파일 생성
                        sh """
                        ssh -o StrictHostKeyChecking=no ${TARGET_EC2} << EOF

                            # 기존 컨테이너 중지 및 제거
                            docker stop pinpung-ai-container || true
                            docker rm pinpung-ai-container || true

                            # 새 컨테이너 실행
                            docker pull ${ECR_REPO}:${DOCKER_IMAGE_TAG}

                            # Docker 컨테이너 실행 시 환경변수 직접 전달
                            docker run -d -p 8000:8000 \
                                -e OPENAI_API_KEY=${openaiApiKey} \
                                -e MYSQL_HOST=${mysqlHost} \
                                -e MYSQL_PORT=${mysqlPort} \
                                -e MYSQL_USER=${mysqlUser} \
                                -e MYSQL_PASSWORD=${mysqlPassword} \
                                -e MYSQL_DATABASE=${mysqlDatabase} \
                                --name pinpung-ai-container ${ECR_REPO}:${DOCKER_IMAGE_TAG}
                        EOF
                        """
                        }
                    }
                }
            }
    }
    post {
        success {
            echo 'AI Deployment successful!'
        }
        failure {
            echo 'AI Deployment failed.'
        }
        always {
            script {
                // Docker 리소스 정리
                sh "docker system prune -af --volumes"
            }
        }
    }
}
