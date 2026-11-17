
pipeline {
    agent any

    environment {
        IMAGE_NAME = 'skill-intelligence-platform'
        IMAGE_TAG = "${BUILD_NUMBER}"
        VENV = '.venv'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Create Virtual Environment') {
            steps {
                sh 'python3 -m venv ${VENV}'
                sh '${VENV}/bin/python -m pip install --upgrade pip'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '${VENV}/bin/pip install -r requirements.txt'
                sh '${VENV}/bin/pip install pytest bandit'
            }
        }

        stage('Automated Tests') {
            steps {
                sh '${VENV}/bin/python -m pytest -v'
            }
        }

        stage('Security Scan') {
            steps {
                sh '${VENV}/bin/python -m bandit -r app.py -ll'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .'
            }
        }

        stage('Deployment Approval') {
            steps {
                input message: 'Approve deployment to staging environment?'
            }
        }

        stage('Deploy to Staging') {
            steps {
                sh '''
                    docker rm -f skill-platform-staging || true
                    docker run -d --name skill-platform-staging \
                    -p 5002:5000 \
                    ${IMAGE_NAME}:${IMAGE_TAG}
                '''
            }
        }
    }

    post {
        success {
            echo 'Pipeline successful. Staging deployment is ready.'
        }
        failure {
            echo 'Pipeline failed. Check Console Output for details.'
        }
        always {
            echo 'Build and test process completed.'
        }
    }
}
