import logging
import os
import re

from coalib.bears.GlobalBear import GlobalBear
from coalib.misc.Shell import run_shell_command
from coalib.results.Result import Result
from git import Repo


class GitBear(GlobalBear):
    LANGUAGES = {"Git"}
    _BRANCH_NAME_REGEX = re.compile(r"^(?:feature|fix)(?:-RH-(\d+))?(?:-[a-zA-Z0-9]+)+$")
    _COMMIT_MESSAGE_AND_PR_NAME_REGEX = re.compile(r"(?:RH-(\d+):)?.*")
    _COMMIT_LOG_SPLIT = re.compile(r"([^\s]+)\s([^\s]+)\s(?:\(.*\)\s)?(.*)")
    _PR_DESCRIPTION_JIRA_TASK = re.compile(r"https://roihunter\.atlassian\.net/browse/RH-(\d+)")
    _DEPLOY_PR_NAMES = re.compile(r"dev\s*(?:->|to).*master", re.IGNORECASE)
    _MERGE_COMMITS_PREFIX = ("Merge branch", "Merge pull request")
    _MAX_COMMIT_MESSAGE_LENGTH = 72

    def run(self, *args, dependency_results=None, **kwargs):
        logging.debug("GitBear checking commits.")
        repository = Repo(".")

        pr_name = os.environ.get("PR_NAME")
        if pr_name and self._DEPLOY_PR_NAMES.match(pr_name):
            return []

        pr_description = os.environ.get("PR_DESCRIPTION")
        pr_number = os.environ.get("PR_NUMBER")
        try:
            branch_name = os.environ.get("GIT_BRANCH") or str(repository.head.reference)
        except TypeError:
            logging.debug("Couldn't fetch git branch.")
            branch_name = ""

        branch_name_in_jenkins = "origin/pr/{}/head".format(pr_number) if pr_number else branch_name

        return self._check_github(branch_name, branch_name_in_jenkins, pr_name, pr_description)

    def _check_github(self, branch_name, branch_name_in_jenkins, pr_name, pr_description):
        branch_name, task_id_from_branch, is_branch_valid = self._parse_branch(branch_name)
        pr_name, task_id_from_pr_name, is_pr_name_valid = self._parse_pr_name(pr_name)
        task_id_from_jira_url = self._parse_pr_description(pr_description)
        commits = self._parse_commits(branch_name, branch_name_in_jenkins)
        is_jira_task = bool(task_id_from_branch or task_id_from_pr_name or task_id_from_jira_url or any(task_id for _, _, task_id, _ in commits))
        is_dependabot = branch_name.startswith("dependabot")

        branch_errors = []
        if not is_dependabot:
            if not is_branch_valid:
                branch_errors.append("Invalid branch name: " + branch_name + ", pattern: " + self._BRANCH_NAME_REGEX.pattern)
            elif is_jira_task and task_id_from_branch is None:
                branch_errors.append("Missing JIRA task number in branch name")

        commits_errors = []
        for commit_id, message, task_id, is_commit_message_valid in commits:
            errors = []
            if not is_commit_message_valid:
                errors.append("Invalid commit message: " + message + ", pattern: " + self._COMMIT_MESSAGE_AND_PR_NAME_REGEX.pattern)
            if len(message) > self._MAX_COMMIT_MESSAGE_LENGTH:
                errors.append("Commit message too long, max length: " + str(self._MAX_COMMIT_MESSAGE_LENGTH) + ", actual length: " + str(len(message)))
            if is_jira_task:
                if not task_id:
                    errors.append("Missing JIRA task number at the beginning of commit message")
                elif task_id != task_id_from_branch and task_id_from_branch is not None:
                    errors.append("JIRA task number from commit message differs from JIRA task number in branch name")

            if errors:
                commits_errors.append(commit_id + " " + message + "\n\t\t" + "\n\t\t".join(errors))

        pr_name_errors = []
        if pr_name:
            if not is_pr_name_valid:
                pr_name_errors.append("Invalid PR name: " + pr_name + ", pattern: " + self._COMMIT_MESSAGE_AND_PR_NAME_REGEX.pattern)

            if is_jira_task:
                if not task_id_from_pr_name:
                    pr_name_errors.append("Missing JIRA task number at the beginning of PR name")
                elif task_id_from_pr_name != task_id_from_branch and task_id_from_branch is not None:
                    pr_name_errors.append("JIRA task number from PR name differs from JIRA task number in branch name")

        pr_description_errors = []
        if pr_description:
            if is_jira_task:
                if not task_id_from_jira_url:
                    pr_description_errors.append("Missing url to JIRA task at the beginning of the PR description")
                elif task_id_from_jira_url != task_id_from_branch and task_id_from_branch is not None:
                    pr_description_errors.append("JIRA task number from PR description differs from JIRA task number in branch name")

        result = "{}{}{}{}".format(
            "BRANCH NAME WARNINGS:\n\t" + "\n\t".join(branch_errors) + "\n\n" if branch_errors else "",
            "COMMITS WARNINGS:\n\t" + "\n\t".join(commits_errors) + "\n\n" if commits_errors else "",
            "PR NAME WARNINGS:\n\t" + "\n\t".join(pr_name_errors) + "\n\n" if pr_name_errors else "",
            "PR DESCRIPTION WARNINGS:\n\t" + "\n\t".join(pr_description_errors) if pr_description_errors else "",
        )

        return [Result(origin="GitBear", message=result)] if result else []

    def _parse_branch(self, branch_name):
        branch_name_match = self._BRANCH_NAME_REGEX.match(branch_name)
        if branch_name_match is None:
            return branch_name, None, False
        else:
            task_id = branch_name_match.group(1)
            return branch_name, task_id, True

    def _parse_commits(self, branch_name, branch_name_in_jenkins):
        commits_logs = run_shell_command("git log --decorate --oneline --source --all -n 1000")[0]
        commits = []
        for commit_log in commits_logs.split("\n"):
            if not commit_log:
                continue
            commit_log = self._COMMIT_LOG_SPLIT.match(commit_log)
            commit_id, branch_info, message = commit_log.group(1), commit_log.group(2), commit_log.group(3)

            if (branch_name not in branch_info and branch_name_in_jenkins not in branch_info) or message.startswith(self._MERGE_COMMITS_PREFIX):
                continue

            commit_message_match = self._COMMIT_MESSAGE_AND_PR_NAME_REGEX.match(message)
            if commit_message_match is None:
                commits.append((commit_id, message, None, False))
            else:
                task_id = commit_message_match.group(1)
                commits.append((commit_id, message, task_id, True))

        return commits

    def _parse_pr_name(self, pr_name):
        if pr_name is None:
            return None, None, False

        pr_name_match = self._COMMIT_MESSAGE_AND_PR_NAME_REGEX.match(pr_name)
        if pr_name_match is None:
            return pr_name, None, False
        else:
            task_id = pr_name_match.group(1)
            return pr_name, task_id, True

    def _parse_pr_description(self, pr_description):
        if not pr_description:
            return None

        pr_description = pr_description.strip().split("\\r\\n")
        jira_url_match = self._PR_DESCRIPTION_JIRA_TASK.match(pr_description[0])
        task_id = jira_url_match.group(1) if jira_url_match else None

        return task_id
