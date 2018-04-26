def sendSlackNotification(String branch_name, String color) {
    withCredentials([string(credentialsId: 'slack-bot-token', variable: 'slack_token')]) {
        message = "Gold Digger $branch_name is deployed."
        slackSend channel: 'python-alerts', message: message, color: "$color", token: slack_token, botUser: true
    }
}

return this
