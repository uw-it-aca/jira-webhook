# jira-webhook

Let JIRA know what's going on!

This is a GitHub webhook that updates JIRA issues with commit information.  To use it, add the JIRA issue ID (COOLPROJ-12345) to your commit messages. Then you can do a JIRA search like:

project = COOLPROJ and comment ~ "Commit on branch refs/heads/qa"

and know what issues have been merged onto qa.
