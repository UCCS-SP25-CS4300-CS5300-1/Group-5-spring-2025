import os
import json
import textwrap
from git import Repo
from github import Github, GithubException
from openai import OpenAI


openai.api_key = os.getenv("OPENAI_API_KEY")
TOKEN_LIMIT = 2048  


def get_file_content(file_path):
    """Reads the content of a file."""
    with open(file_path, 'r') as file:
        return file.read()

def get_changed_files(pr):
    """
    Fetches the changed files from a pull request by cloning the repository
    and diffing the base and head branches.
    """
    repo = Repo.clone_from(pr.base.repo.clone_url, to_path='./repo', branch=pr.head.ref)
    base_ref = f"origin/{pr.base.ref}"
    head_ref = f"origin/{pr.head.ref}"
    diffs = repo.git.diff(base_ref, head_ref, name_only=True).splitlines()

    files = {}
    for file_path in diffs:
        try:
            full_path = os.path.join('./repo', file_path)
            files[file_path] = get_file_content(full_path)
        except Exception as e:
            print(f"Failed to read {file_path}: {e}")
    return files

def send_to_openai(files):
    """
    Sends the changed files to OpenAI for review.
    The code is chunked based on TOKEN_LIMIT to avoid exceeding token limits.
    """
    code = '\n'.join(files.values())
    chunks = textwrap.wrap(code, TOKEN_LIMIT)
    reviews = []
    for chunk in chunks:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "You are assigned as a code reviewer. Your responsibility is to review the provided code and offer recommendations for enhancement. "
                            "Identify any problematic code snippets, highlight potential issues, and evaluate the overall quality of the code you review:\n" + chunk
                        )
                    }
                ]
            )
            reviews.append(response['choices'][0]['message']['content'])
        except Exception as e:
            print(f"Error during OpenAI request: {e}")
    return "\n".join(reviews)

def post_comment(pr, comment):
    """Posts a comment on the pull request with the review."""
    try:
        pr.create_issue_comment(comment)
    except GithubException as e:
        print(f"Failed to post comment: {e}")

def main():
    """
    Main function orchestrating the code review workflow:
      1. Loads the event JSON to get repository and pull request details.
      2. Instantiates the GitHub client using a token.
      3. Retrieves the pull request and its changed files.
      4. Sends the code to OpenAI for review and posts the review as a comment.
    """
    event_path = os.getenv('GITHUB_EVENT_PATH')
    if not event_path:
        raise ValueError("GITHUB_EVENT_PATH environment variable not set.")

    with open(event_path) as json_file:
        event = json.load(json_file)

    # Use the default GITHUB_TOKEN or fall back to an alternative token (e.g., MY_GITHUB_TOKEN)
    token = os.getenv('GITHUB_TOKEN') or os.getenv('MY_GITHUB_TOKEN')
    if not token:
        raise ValueError("No GitHub token provided. Set GITHUB_TOKEN or MY_GITHUB_TOKEN environment variable.")

    g = Github(token)
    repo_full_name = event['repository']['full_name']
    pr_number = event.get('number')
    if pr_number is None:
        raise ValueError("Pull request number not found in event data.")

    try:
        repo = g.get_repo(repo_full_name)
        pr = repo.get_pull(pr_number)
    except GithubException as e:
        print(f"Error retrieving pull request: {e}")
        print("This may be due to insufficient token permissions. Ensure your workflow's permissions include access to pull requests.")
        raise

    files = get_changed_files(pr)
    if not files:
        print("No changed files found in the pull request.")
        return

    review = send_to_openai(files)
    post_comment(pr, review)

if __name__ == "__main__":
    main()
