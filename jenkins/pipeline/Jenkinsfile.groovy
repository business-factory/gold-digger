pipeline {
    agent {label 'docker01'}

    options {
        ansiColor colorMapName: 'XTerm'
    }

    parameters {
        booleanParam(name: 'build_image', defaultValue: true, description: 'Build image and upload it to Docker registry')
        booleanParam(name: 'send_notification', defaultValue: true, description: 'Send notification about deploy to Slack')
    }

    stages {
        stage('Build') {
            when {
                expression {
                    return params.build_image
                }
            }
            steps {
                sh "docker build --rm=true -t roihunter.azurecr.io/golddigger/master ."
                withCredentials([string(credentialsId: 'docker-registry-azure', variable: 'DRpass')]) {
                    sh 'docker login roihunter.azurecr.io -u roihunter -p "$DRpass"'
                    sh("""
                        for tag in $BUILD_NUMBER latest; do
                            docker tag docker tag roihunter.azurecr.io/golddigger/master roihunter.azurecr.io/golddigger/master:\${tag}
                            docker push roihunter.azurecr.io/golddigger/master:\${tag}
                            docker rmi roihunter.azurecr.io/golddigger/master:\${tag}
                        done
                    """)
                }
            }
        }

        stage('Deploy containers') {
            steps {
                withCredentials([file(credentialsId: 'jenkins-master-kubeconfig', variable: 'kube_config')]) {
                    kubernetesDeploy(
                        configs: '**/kubernetes/gold-digger-deployment.yaml,**/kubernetes/gold-digger-service.yaml,**/kubernetes/gold-digger-cron-deployment.yaml',
                        dockerCredentials: [
                             [credentialsId: 'docker-azure-credentials', url: 'http://roihunter.azurecr.io']
                        ],
                        kubeConfig: [
                            path: "$kube_config"
                        ],
                        secretName: 'regsecret',
                        ssh: [
                            sshCredentialsId: '*',
                            sshServer: ''
                        ],
                        textCredentials: [
                            certificateAuthorityData: '',
                            clientCertificateData: '',
                            clientKeyData: '',
                            serverUrl: 'https://'
                        ]
                    )
                }
            }
        }

        stage('Send notification') {
            when {
                expression {
                    return params.send_notification
                }
            }
            steps {
                withCredentials([string(credentialsId: 'slack-bot-token', variable: 'slackToken')]) {
                    slackSend channel: 'deploy', message: 'GoldDigger application was deployed', color: '#0E8A16', token: slackToken, botUser: true
                }
            }
        }
    }
    post {
        always {
            // Clean Workspace
            cleanWs()
        }
    }
}
