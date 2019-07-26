def github

pipeline {
    agent {
        label "docker01"
    }

    options {
        timeout(time: 1, unit: "HOURS")
        ansiColor colorMapName: "XTerm"
    }

    stages {
        stage("Load libraries and global variables") {
            steps {
                script {
                    def rootDir = pwd()
                    github = load "${rootDir}/jenkins/pipeline/_github.groovy"
                }
            }
        }

        stage("Run nazi coala") {
            steps {
                sh 'docker run --rm -t -v "$(pwd):/app" --workdir=/app coala/base:0.11 coala -d bears --non-interactive --no-color'
            }
        }

        stage("Run calm coala") {
            steps {
                script {
                    def result = sh(
                        returnStdout: true,
                        script: '''docker run --rm -t \
                            -e "GIT_BRANCH=$ghprbSourceBranch" \
                            -e "PR_NAME=$ghprbPullTitle" \
                            -e "PR_DESCRIPTION=$ghprbPullLongDescription" \
                            -e "PR_NUMBER=$ghprbPullId" \
                            -v "$(pwd):/app" \
                            --workdir=/app coala/base:0.11 coala -d bears \
                            --non-interactive --no-color --no-autoapply-warn \
                            -c .coafile_without_fails || exit 0'''
                    ).trim()

                    List commentsURLToDelete = github.getCommentsURLToDelete("Coala found some errors that you can fix.")
                    commentsURLToDelete.each {
                        github.deleteComment(it)
                    }

                    if (result.contains("[NORMAL] GitBear")) {
                        String message = formatCoalaMessage(result)
                        github.sendCommentToGit(message)
                    }
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}

/**
 * Message is formatted to look "good" on github.
 **/
String formatCoalaMessage(message) {
    message = message.replaceAll("Executing section GitBear...", "Coala found some errors that you can fix.")
    message = message.replaceAll("\"", "&quot;")
    message = message.replaceAll("'", "&#39;")
    message = message.replaceAll("\n", "<BR>")
    message = message.replaceAll("\r", "<BR>")
    message = message.replaceAll("<BR><BR>", "<BR>")
    message = message.replaceAll("\t", "&nbsp; &nbsp; ")
    message = message.replaceAll("\\s\\s+", "&nbsp; &nbsp; &nbsp; ")
    message = message.substring(0, message.length() - 4)
    message = message.replaceAll("\\\\", "\\\\\\\\")
    message = message.replaceAll("Executing section cli...", "")

    return message
}
