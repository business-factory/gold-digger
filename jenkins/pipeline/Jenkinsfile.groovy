pipeline {
    agent {
        label 'docker01'
    }

    options {
        ansiColor colorMapName: 'XTerm'
    }

    parameters {
        booleanParam(
            name: 'SEND_SLACK_NOTIFICATION',
            defaultValue: true,
            description: 'Send notification about deploy to Slack.'
        )
    }

    environment {
        BRANCH_NAME = env.GIT_BRANCH.replaceFirst("origin/", "")
    }

    stages {
        stage("Build Docker image") {
            steps {
                script {
                    def rootDir = pwd()
                    def build = load "${rootDir}/jenkins/pipeline/_build.groovy"
                    build.buildDockerImage(env.BRANCH_NAME)
                }
            }
        }

        stage('Deploy service to Kubernetes') {
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

        stage('Send Slack notification') {
            when {
                expression {
                    return params.SEND_SLACK_NOTIFICATION
                }
            }
            steps {
                script {
                    def rootDir = pwd()
                    def utils = load "${rootDir}/jenkins/pipeline/_utils.groovy"
                    utils.sendSlackNotification(env.BRANCH_NAME, '#0E8A16')
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
