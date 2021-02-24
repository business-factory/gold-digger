def sendSlackNotification(String color, String message) {
    slackSend channel: "python-alerts", message: message, color: "$color", tokenCredentialId: "slack-bot-token", botUser: true
}

return this
