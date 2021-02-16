def currentMaster, doRelease, github, utils

pipeline {
    agent {
        label "docker01"
    }

    libraries {
        lib("jenkins-pipes@master")
    }

    options {
        ansiColor colorMapName: "XTerm"
    }

    parameters {
        booleanParam(
            name: "FEATURE_RELEASE",
            defaultValue: false,
            description: "Whether feature or bug fix should be released."
        )
        string(
            name: "RELEASE_VERSION",
            defaultValue: "",
            description: "Specify release version number. (FEATURE_RELEASE will be ignored)"
        )
    }

    environment {
        BRANCH_NAME = env.GIT_BRANCH.replaceFirst("origin/", "")
    }

    stages {
        stage("Load libraries and global variables") {
            steps {
                script {
                    def rootDir = pwd()
                    github = load "${rootDir}/jenkins/pipeline/_github.groovy"
                    utils = load "${rootDir}/jenkins/pipeline/_utils.groovy"
                }
            }
        }

        stage("Determine next app version") {
            steps {
                script {
                    doRelease = github.getReleasePreview()
                    currentMaster = github.getLatestRelease()

                    try {
                        if (doRelease) {
                            // Check if version was specified manually
                            if (params.RELEASE_VERSION != "") {
                                // At least basic validation has to be done first
                                def versionRegex = /^\d+\.\d+\.\d+$/
                                def versionMatcher = params.RELEASE_VERSION =~ versionRegex
                                if (!versionMatcher.matches()) {
                                    error("Provided version is badly formatted. Enter a valid version or leave it empty for release to decide automatically.")
                                } else {
                                    env.APP_VERSION = params.RELEASE_VERSION
                                }

                            } else if (params.FEATURE_RELEASE) {
                                def currentMasterMajorReleaseString = currentMaster.substring(0, currentMaster.indexOf("."))
                                def currentMasterMinorReleaseString = currentMaster.substring(currentMaster.indexOf(".") + 1, currentMaster.lastIndexOf("."))
                                int currentMasterMinorReleaseNumber = currentMasterMinorReleaseString.toInteger()
                                int newMasterMinorReleaseNumber = currentMasterMinorReleaseNumber + 1
                                env.APP_VERSION = currentMasterMajorReleaseString + "." + newMasterMinorReleaseNumber.toString() + ".0"

                            } else {
                                // First number is the major release (hardly ever changes),
                                // middle is minor (changes on feature master deploys),
                                // last is build (increments on every build)
                                def currentMasterMajorAndMinorReleaseString = currentMaster.substring(0, currentMaster.lastIndexOf(".") + 1)
                                def currentMasterBuildString = currentMaster.substring(currentMaster.lastIndexOf(".") + 1)
                                int currentMasterBuildNumber = currentMasterBuildString.toInteger()
                                int newMasterBuildNumber = currentMasterBuildNumber + 1
                                env.APP_VERSION = currentMasterMajorAndMinorReleaseString + newMasterBuildNumber.toString()
                            }

                        } else {
                            env.APP_VERSION = currentMaster
                        }

                        println(env.APP_VERSION)

                    } catch (err) {
                        println("Failed to determine next app version. Error: " + err)
                    }
                }
            }
        }

        stage("Build Docker image") {
            steps {
                script {
                    dockerBuild env.BRANCH_NAME, "golddigger"
                }
            }
        }

        stage("Deploy API") {
            steps {
                script {
                    withCredentials([file(credentialsId: "jenkins-roihunter-master-kubeconfig", variable: "kube_config")]) {
                        sh '''
                        sed -i "s/\\$BUILD_NUMBER/$BUILD_NUMBER/g" kubernetes/gold-digger-api-deployment.yaml
                        sed -i "s/\\$BUILD_NUMBER/$BUILD_NUMBER/g" kubernetes/gold-digger-cron-deployment.yaml
                        sed -i "s/\\$APP_VERSION/$APP_VERSION/g" kubernetes/gold-digger-api-deployment.yaml
                        sed -i "s/\\$APP_VERSION/$APP_VERSION/g" kubernetes/gold-digger-cron-deployment.yaml
                        kubectl --kubeconfig="$kube_config" apply -Rf kubernetes/
                        kubectl --kubeconfig="$kube_config" rollout status deployment/gold-digger-deployment --timeout 2m
                        kubectl --kubeconfig="$kube_config" rollout status deployment/gold-digger-cron-deployment --timeout 2m
                        '''
                    }
                }
            }
        }

        stage("Do GitHub release") {
            steps {
                script {
                    try {
                        if (doRelease) {
                            def body = "version=${env.APP_VERSION}"
                            withCredentials([string(credentialsId: "releaser-authorization", variable: "releaserAuthorization")]) {
                                httpRequest(
                                    customHeaders: [[name: "Authorization", value: releaserAuthorization],
                                    [name: "Content-Type", value: "application/x-www-form-urlencoded"]],
                                    ignoreSslErrors: true,
                                    httpMode: "POST",
                                    requestBody: body,
                                    url: """https://helpers.roihunter.com/helpers/releaser/gold-digger/release/master/$currentMaster...master"""
                                )
                            }

                        } else {
                            println("Not doing the release, because there were no commits to release.")
                        }

                    } catch (err) {
                        utils.sendSlackNotification(
                            "#FF0000",
                            "Gold Digger ${env.BRANCH_NAME} release failed. Please release changes manually at https://helpers.roihunter.com/helpers/releaser/gold-digger/"
                        )
                        println("GitHub release failed. Error: " + err)
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
