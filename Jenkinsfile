pipeline {
    agent any

    environment {
        AWS_DEFAULT_REGION    = 'ap-southeast-2'
        AWS_ACCOUNT_ID        = credentials('aws-account-id')
        AWS_ACCESS_KEY_ID     = credentials('aws-access-key-id')
        AWS_SECRET_ACCESS_KEY = credentials('aws-secret-key')
        ECR_REGISTRY          = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com"
        ECR_REPO              = 'task-manager'
        IMAGE_TAG             = "build-${BUILD_NUMBER}"
        FULL_IMAGE            = "${ECR_REGISTRY}/${ECR_REPO}:${IMAGE_TAG}"
        SERVER_IP             = '15.134.98.247'
    }

    options {
        timeout(time: 20, unit: 'MINUTES')
        timestamps()
    }

    stages {

        stage('Checkout') {
            steps {
                echo "Checking out code from GitHub"
                checkout scm
            }
        }

        stage('Test') {
            steps {
                echo "Running tests"
                sh '''
                    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
                    find . -name "*.pyc" -delete 2>/dev/null || true
                    python3 -m venv /tmp/test-venv
                    . /tmp/test-venv/bin/activate
                    pip install -r app/requirements.txt pytest
                    cd app
                    python3 -m pytest test_app.py -v
                    deactivate
                '''
            }
        }

        stage('Docker Build') {
            steps {
                echo "Building Docker image: ${FULL_IMAGE}"
                sh '''
                    docker buildx create --use --name amd64-builder || true
                    docker buildx build \
                        --platform linux/amd64 \
                        --provenance=false \
                        --load \
                        -t $FULL_IMAGE \
                        .
                    docker tag $FULL_IMAGE $ECR_REGISTRY/$ECR_REPO:latest
                '''
            }
        }

        stage('Docker Push') {
            steps {
                echo "Pushing image to AWS ECR"
                sh '''
                    aws ecr get-login-password --region $AWS_DEFAULT_REGION | \
                    docker login --username AWS --password-stdin $ECR_REGISTRY
                    docker push $FULL_IMAGE
                    docker push $ECR_REGISTRY/$ECR_REPO:latest
                '''
            }
        }

        stage('Deploy') {
            steps {
                echo "Deploying to Kubernetes"
                sshagent(['ssh-private-key']) {
                    sh '''
                        ECR_PASSWORD=$(aws ecr get-login-password --region $AWS_DEFAULT_REGION)

                        ssh -o StrictHostKeyChecking=no ubuntu@$SERVER_IP \
                            ECR_REGISTRY="$ECR_REGISTRY" \
                            ECR_PASSWORD="$ECR_PASSWORD" \
                            FULL_IMAGE="$FULL_IMAGE" \
                            bash -s << 'ENDSSH'

                            export KUBECONFIG=/home/ubuntu/.kube/config

                            echo "Refreshing ECR pull secret..."
                            kubectl delete secret ecr-secret --ignore-not-found
                            kubectl create secret docker-registry ecr-secret \
                                --docker-server=$ECR_REGISTRY \
                                --docker-username=AWS \
                                --docker-password=$ECR_PASSWORD

                            echo "Updating image to $FULL_IMAGE..."
                            kubectl set image deployment/task-manager-app \
                                task-manager=$FULL_IMAGE

                            echo "Waiting for rollout..."
                            kubectl rollout status deployment/task-manager-app --timeout=180s

                            echo "=== POD STATUS ==="
                            kubectl get pods -o wide
ENDSSH
                    '''
                }
            }
        }

        stage('Verify') {
            steps {
                echo "Verifying deployment"
                sh '''
                    sleep 10
                    curl -f --retry 5 --retry-delay 5 \
                        http://$SERVER_IP:30080/health
                    echo "APP IS LIVE at http://$SERVER_IP:30080"
                '''
            }
        }
    }

    post {
        success { echo "Pipeline succeeded! App is deployed." }
        failure { echo "Pipeline FAILED. Check the logs above." }
        always  { cleanWs() }
    }
}