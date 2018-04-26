def buildDockerImage(String branch_name) {
    // build image
    sh "docker build --tag roihunter.azurecr.io/golddigger/${branch_name}:$BUILD_NUMBER  --cache-from roihunter.azurecr.io/golddigger/${branch_name}:latest ."

    withCredentials([string(credentialsId: 'docker-registry-azure', variable: 'DRpass')]) {
        // upload versioned image to registry
        sh 'docker login roihunter.azurecr.io -u roihunter -p "$DRpass"'
        sh "docker push roihunter.azurecr.io/golddigger/${branch_name}:$BUILD_NUMBER"

        // upload latest image to registry
        sh "docker tag roihunter.azurecr.io/golddigger/${branch_name}:$BUILD_NUMBER roihunter.azurecr.io/golddigger/${branch_name}:latest"
        sh "docker push roihunter.azurecr.io/golddigger/${branch_name}:latest"
    }
}

return this
