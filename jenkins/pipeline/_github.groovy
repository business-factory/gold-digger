import groovy.json.JsonSlurper

/**
 * Get urls of all comments in GitHub PR
 * Only comments starting with specific prefix will be returned
 **/
void getCommentsURLToDelete(commentPrefix) {
    String commentsAsString = ""
    try {
        withCredentials([string(credentialsId: "github_token_write_access_to_pr", variable: "gold_digger_github_token")]) {
            commentsAsString = sh(
                script: "curl -s -H \"Authorization: token $gold_digger_github_token\" \"https://api.github.com/repos/roihunter/gold-digger/issues/${ghprbPullId}/comments\" ",
                returnStdout: true
            )
        }
    } catch (e) {
        echo "Script (get comments from GitHub) returned exception: " + e
        return
    }

    JsonSlurper jsonSlurper = new JsonSlurper()
    def comments = jsonSlurper.parseText(commentsAsString)

    if ( !(comments instanceof List) ) {
        echo "Can't parse JSON - expected list of comments: '$commentsAsString'"
        return
    }

    List<String> commentsURLToDelete = new ArrayList<String>()
    comments.each {
        if ( it.user.login == "DavidPrexta" && it.body.startsWith(commentPrefix) ) {
            commentsURLToDelete.add(it.url)
        }
    }

    return commentsURLToDelete
}

/**
 * Delete comment in github PR
 **/
void deleteComment(String commentUrl) {
    try {
        withCredentials([string(credentialsId: "github_token_write_access_to_pr", variable: "gold_digger_github_token")]) {
            sh(
                script: "curl -s -H \"Authorization: token $gold_digger_github_token\" -X DELETE \"$commentUrl \" || true",
                returnStdout: true
            )
        }
    } catch (e) {
        echo "Script (delete comment from GitHub) returned exception: " + e
    }
}

/**
 * Send comment into GitHub PR
 **/
void sendCommentToGit(String message) {
    try {
        withCredentials([string(credentialsId: "github_token_write_access_to_pr", variable: "gold_digger_github_token")]) {
            sh(
                script: "curl -s -H \"Authorization: token $gold_digger_github_token\" -X POST --data '{\"body\":\"${message}\"}\' \"https://api.github.com/repos/roihunter/gold-digger/issues/${ghprbPullId}/comments\" ",
                returnStdout: true
            )
        }
    } catch (e) {
        echo "Script (send comment to git) returned exception: " + e
    }
}

return this
