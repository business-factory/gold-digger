pipeline {
    agent {
        label 'docker01'
    }

    options {
        ansiColor colorMapName: 'XTerm'
    }

    parameters {
        string(
                name: 'APP_SERVER',
                defaultValue: '10.10.10.185',
                description: 'Deploy container to this server.'
        )
        string(
                name: 'DATABASE_HOST',
                defaultValue: '10.10.10.122',
                description: 'Postgresql DB host.'
        )
        string(
                name: 'DATABASE_PORT',
                defaultValue: '55432',
                description: 'Postgresql DB port.'
        )
        string(
                name: "COMMAND",
                defaultValue: "python -m gold_digger --help",
                description: "One time command to be executed"
        )
    }

    stages {
        stage('Run container') {
            steps {
                withCredentials([
                    string(credentialsId: 'docker-registry-azure', variable: 'DRpass'),
                    string(
                        credentialsId: 'gold_digger_master_secrets_currency_layer_access_key',
                        variable: 'gold_digger_master_secrets_currency_layer_access_key'
                    ),
                    usernamePassword(
                        credentialsId: 'gold_digger_master_database',
                        usernameVariable: 'gold_digger_master_db_user',
                        passwordVariable: 'gold_digger_master_db_password'
                    )
                ]) {
                    script {
                        def server = params['APP_SERVER']
                        def database_host = params['DATABASE_HOST']
                        def database_port = params['DATABASE_PORT']
                        def command_name = getContainerName("${params.COMMAND}")
                        def command = "${params.COMMAND}"

                        sshagent(['5de2256c-107d-4e4a-a31e-2f33077619fe']) {
                            sh """ssh -oStrictHostKeyChecking=no -t -t jenkins@${server} <<EOF
                                docker login roihunter.azurecr.io -u roihunter -p "$DRpass"
                                docker pull roihunter.azurecr.io/golddigger/master
                                docker run --rm -d \
                                    -e "GOLD_DIGGER_PROFILE=master" \
                                    -e GOLD_DIGGER_DATABASE_HOST='''$database_host''' \
                                    -e GOLD_DIGGER_DATABASE_PORT='''$database_port''' \
                                    -e GOLD_DIGGER_DATABASE_USER='''$gold_digger_master_db_user''' \
                                    -e GOLD_DIGGER_DATABASE_PASSWORD='''$gold_digger_master_db_password''' \
                                    -e GOLD_DIGGER_SECRETS_CURRENCY_LAYER_ACCESS_KEY='''$gold_digger_master_secrets_currency_layer_access_key''' \
                                    --hostname="golddigger-one-time-${command_name}-${env.BUILD_ID}" \
                                    --name="golddigger-one-time-${command_name}-${env.BUILD_ID}" \
                                    roihunter.azurecr.io/golddigger/master \
                                    ${command}

                                exit
                                EOF"""
                        }
                    }
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

// Extract script name or first cli argument after "python -m gold_digger"
// Examples:
//      python /tools/migration/db-migrate.py -> db-migrate
//      python -m gold_digger cron -> cron
String getContainerName(String command) {
    def command_arguments = command.replaceAll( /\bpython -m gold_digger /, '' ).tokenize(" ")
    if(command_arguments.size() > 1 && command_arguments[0] == "python"){
        def command_path = command_arguments[1].tokenize("/")
        return (command_path[-1].endsWith(".py")) ? command_path[-1][0..-4] : command_path[-1]
    }
    else {
        return command_arguments[0]
    }
}
