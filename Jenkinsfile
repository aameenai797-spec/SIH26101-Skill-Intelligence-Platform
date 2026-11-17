pipeline {
    agent any
    environment {
        IMAGE_NAME = 'skill-intelligence-platform'
        IMAGE_TAG = "${BUILD_NUMBER}"
    }
    stages {
        stage('Checkout') {
            steps { checkout scm }
        }
        stage('Install Dependencies') {
            steps { sh 'python3 -m pip install --user -r requirements.txt' }
        }
        stage('Automated Tests') {
            steps { sh 'python3 -m pytest -v' }
        }
        stage('Security Scan') {
            steps { sh 'python3 -m bandit -r app.py -ll' }
        }
        stage('Build Docker Image') {
            steps { sh 'docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .' }
        }
        stage('Deployment Approval') {
            steps { input message: 'Approve deployment to staging environment?' }
        }
        stage('Deploy to Staging') {
            steps {
                sh 'docker rm -f skill-platform-staging || true'
                sh 'docker run -d --name skill-platform-staging -p 5001:5000 -e SECRET_KEY="$SECRET_KEY" ${IMAGE_NAME}:${IMAGE_TAG}'
            }
        }
    }
    post {
        success { echo 'Pipeline successful. Staging deployment is ready.' }
        failure { echo 'Pipeline failed. Previous running container is not replaced.' }
        always { echo 'Build and test process completed.' }
    }
}
