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
                sh "docker build --rm=true -t golddigger-stage ."
            }
        }

        stage('Prepare and upload to registry ') {
            when {
                expression {
                    return params.build_image
                }
            }
            steps {
                withCredentials([string(credentialsId: 'docker-registry-azure', variable: 'DRpass')]) {
                    sh 'docker login roihunter.azurecr.io -u roihunter -p "$DRpass"'
                    sh "docker tag golddigger-stage roihunter.azurecr.io/golddigger/stage"
                    sh "docker push roihunter.azurecr.io/golddigger/stage"
                    sh "docker rmi golddigger-stage"
                    sh "docker rmi roihunter.azurecr.io/golddigger/stage"
                }
            }
        }

        stage('Deploy containers') {
            steps {
                
                withCredentials([file(credentialsId: 'jenkins-stage-kubeconfig', variable: 'kube_config')]) {
                    kubernetesDeploy(
                        configs: '**/kubernetes/gold-digger-deployment.yaml,**/kubernetes/gold-digger-service.yaml',
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
