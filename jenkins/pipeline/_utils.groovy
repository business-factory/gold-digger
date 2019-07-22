def sendSlackNotification(String color, String message) {
    withCredentials([string(credentialsId: 'slack-bot-token', variable: 'slack_token')]) {
        slackSend channel: 'python-alerts', message: message, color: "$color", token: slack_token, botUser: true
    }
}

return this
