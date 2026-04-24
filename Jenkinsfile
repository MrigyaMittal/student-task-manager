pipeline {
    agent any

    environment {
        AWS_DEFAULT_REGION      = 'ap-southeast-2'
        AWS_ACCOUNT_ID          = credentials('aws-account-id')
        AWS_ACCESS_KEY_ID       = credentials('aws-access-key-id')
        AWS_SECRET_ACCESS_KEY   = credentials('aws-secret-key')
        ECR_REGISTRY            = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com"
        ECR_REPO                = 'task-manager'
        IMAGE_TAG               = "build-${BUILD_NUMBER}"
        FULL_IMAGE              = "${ECR_REGISTRY}/${ECR_REPO}:${IMAGE_TAG}"
        SSH_PUBLIC_KEY          = credentials('ssh-public-key-text')
    }

    options {
        timeout(time: 45, unit: 'MINUTES')
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
                    python3 -m venv /tmp/test-venv
                    . /tmp/test-venv/bin/activate
                    pip install -r app/requirements.txt pytest
                    python3 -m pytest app/test_app.py -v
                    deactivate
                '''
            }
        }

        stage('Docker Build') {
            steps {
                echo "Building Docker image: ${FULL_IMAGE}"
                sh '''
                    docker build -t $FULL_IMAGE .
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

                    aws ecr describe-repositories --repository-names $ECR_REPO \
                        --region $AWS_DEFAULT_REGION || \
                    aws ecr create-repository --repository-name $ECR_REPO \
                        --region $AWS_DEFAULT_REGION

                    docker push $FULL_IMAGE
                    docker push $ECR_REGISTRY/$ECR_REPO:latest
                '''
            }
        }

        stage('Terraform') {
            steps {
                echo "Provisioning AWS infrastructure"
                dir('terraform') {
                    sh '''
                        terraform init
                        terraform plan -var="ssh_public_key=$SSH_PUBLIC_KEY" -out=tfplan
                        terraform apply -auto-approve tfplan
                        terraform output -raw server_public_ip > /tmp/server_ip.txt
                        echo "Server IP: $(cat /tmp/server_ip.txt)"
                    '''
                }
            }
        }

        stage('Ansible Configure') {
            steps {
                echo "Configuring server with Ansible"
                sshagent(['ssh-private-key']) {
                    sh '''
                        SERVER_IP=$(cat /tmp/server_ip.txt)
                        echo "Configuring: $SERVER_IP"
                        sleep 200

                        sed "s/SERVER_IP_PLACEHOLDER/$SERVER_IP/" \
                            ansible/inventory.ini > /tmp/inventory.ini

                        ansible-playbook \
                            -i /tmp/inventory.ini \
                            -v \
                            ansible/playbook.yml
                    '''
                }
            }
        }

        stage('Deploy') {
            steps {
                echo "Deploying to Kubernetes"
                sshagent(['ssh-private-key']) {
                    sh '''
                        SERVER_IP=$(cat /tmp/server_ip.txt)

                        sed "s|IMAGE_PLACEHOLDER|$FULL_IMAGE|g" \
                            k8s/deployment.yaml > /tmp/deployment-actual.yaml

                        scp -o StrictHostKeyChecking=no \
                            /tmp/deployment-actual.yaml \
                            k8s/service.yaml \
                            ubuntu@$SERVER_IP:/tmp/

                        ssh -o StrictHostKeyChecking=no \
                            ubuntu@$SERVER_IP "
                            export KUBECONFIG=/home/ubuntu/.kube/config
                            sleep 30
                            kubectl apply --validate=false -f /tmp/deployment-actual.yaml
                            kubectl apply --validate=false -f /tmp/service.yaml
                            kubectl rollout status deployment/task-manager-app --timeout=120s
                        "
                    '''
                }
            }
        }

        stage('Verify') {
            steps {
                echo "Verifying deployment"
                sh '''
                    SERVER_IP=$(cat /tmp/server_ip.txt)
                    sleep 20
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