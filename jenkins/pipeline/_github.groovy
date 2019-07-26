import groovy.json.JsonSlurper

def rootDir = pwd()
utils = load "${rootDir}/jenkins/pipeline/_utils.groovy"

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

/***
 * Check if release is needed, e.g. some commits were made after last release.
 */
boolean getReleasePreview() {
    def parsed, previewRootSlurper, preview
    int totalCommits = 0

    def latestRelease = getLatestRelease()

    try {
        withCredentials([string(credentialsId: "github-authorization", variable: "githubAuthorization")]) {
            preview = httpRequest(
                customHeaders: [[name: "Authorization", value: githubAuthorization]],
                ignoreSslErrors: false,
                url: """https://api.github.com/repos/roihunter/gold-digger/compare/$latestRelease...master}"""
            )
        }

        previewRootSlurper = new JsonSlurper()
        parsed = previewRootSlurper.parseText(preview.getContent())
        totalCommits = parsed.total_commits
        println("Total commits for the release: ${totalCommits}")
    } catch (err) {
        utils.sendSlackNotification(
            "#FF0000",
            "GitHub release preview fetch failed for Gold Digger ${env.BRANCH_NAME}. Please release changes manually at https://py.b.cz/helpers/releaser/gold-digger/"
        )
        println("GitHub release preview failed. Error: " + err)
    }

    return totalCommits > 0
}

def getLatestRelease() {
    def ghResponse, releases, latestRelease, ghRootSlurper, ghParsedResponse

    try {
        // first (pre-)release has to be done manually
        withCredentials([string(credentialsId: "github-authorization", variable: "githubAuthorization")]) {
            ghResponse = httpRequest(
                customHeaders: [[name: "Authorization", value: githubAuthorization]],
                ignoreSslErrors: false,
                url: "https://api.github.com/repos/roihunter/gold-digger/releases"
            )
        }

        ghRootSlurper = new JsonSlurper()
        ghParsedResponse = ghRootSlurper.parseText(ghResponse.getContent())
        releases = ghParsedResponse.find({ !it.prerelease })

        latestRelease = releases.drop(1).tag_name
        return latestRelease
    } catch (err) {
        utils.sendSlackNotification(
            "#FF0000",
            "GitHub release version fetch failed for Gold Digger ${env.BRANCH_NAME}. Please release changes manually at https://py.b.cz/helpers/releaser/gold-digger/"
        )
        println("GitHub release version fetch failed. Error: " + err)
    }
}

return this
