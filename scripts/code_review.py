import os
import openai
from github import Github
import git
import json
import textwrap

#From https://medium.com/@owuordove/github-actions-building-an-end-to-end-ci-cd-pipeline-for-django-dbaaa20dc0ac#id_token=eyJhbGciOiJSUzI1NiIsImtpZCI6IjkxNGZiOWIwODcxODBiYzAzMDMyODQ1MDBjNWY1NDBjNmQ0ZjVlMmYiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJhenAiOiIyMTYyOTYwMzU4MzQtazFrNnFlMDYwczJ0cDJhMmphbTRsamRjbXMwMHN0dGcuYXBwcy5nb29nbGV1c2VyY29udGVudC5jb20iLCJhdWQiOiIyMTYyOTYwMzU4MzQtazFrNnFlMDYwczJ0cDJhMmphbTRsamRjbXMwMHN0dGcuYXBwcy5nb29nbGV1c2VyY29udGVudC5jb20iLCJzdWIiOiIxMDA1ODc3MTYyNzE1Mzg2MzQ5MzYiLCJlbWFpbCI6ImFiaWdhaWxjb253YXkwN0BnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwibmJmIjoxNzQxODQwNTM5LCJuYW1lIjoiQWJpZ2FpbCBDb253YXkiLCJwaWN0dXJlIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jS1VFNGxHOXduSjhLRFJKNHVtUGZMNFVGUWlPa1JDam5CUVlYN2hxR2xOTktxMkhRPXM5Ni1jIiwiZ2l2ZW5fbmFtZSI6IkFiaWdhaWwiLCJmYW1pbHlfbmFtZSI6IkNvbndheSIsImlhdCI6MTc0MTg0MDgzOSwiZXhwIjoxNzQxODQ0NDM5LCJqdGkiOiJjNGJhNmRkNDczZmIyNjVjY2EzZTZhZmExNDQ2Y2QzZmJlYWRkNWRkIn0.QLSAE9vlmm6x4I-G0jCO-x53YiRc5sPxLSaR4LV1XraVsu9wuVxbA_9g4Z62s19mR7-6QLq03P8QkOWKex0PFNzztmiOxZSlXws41Yc4llm-teGamIIYxbbmkEJVAufutzj8N0Beg9jVOr-_UBmQ6tCn3WuP6u-WxEQ4wfX0VjRssJWQz3DsVEkABjOXikeYPL9OHr3EWPD_6pCCWlt8Xnw1qfwzIvppfFqVTrikeAPyWv0DSw2rzu67sCXOQW_c_7PRgmxezx5cHIrwZ0uT49RCTHCrX5a0xAc-v9CqeKH2rbmHS96tJBnF9CruugeugtAE_jVsGU7P8ZalVtkDuQ

# Load OpenAI API key from environment
openai.api_key = os.getenv('OPENAI_API_KEY')

# Set the maximum token limit for GPT-4
TOKEN_LIMIT = 50

def get_file_content(file_path):
    """
    This function reads the content of a file.

    Args:
        file_path (str): The path to the file.

    Returns:
        str: The content of the file.
    """
    with open(file_path, 'r') as file:
        return file.read()

def get_changed_files(pr):
    """
    This function fetches the files that were changed in a pull request.

    Args:
        pr (PullRequest): The pull request object.

    Returns:
        dict: A dictionary containing the file paths as keys and their content as values.
    """
    # Clone the repository and checkout the PR branch
    clone_url = f"https://{os.getenv('GITHUB_TOKEN')}@github.com/{pr.base.repo.full_name}.git"
    repo = git.Repo.clone_from(clone_url, to_path='./repo', branch=pr.head.ref)


    # Get the difference between the PR branch and the base branch
    base_ref = f"origin/{pr.base.ref}"
    head_ref = f"origin/{pr.head.ref}"
    diffs = repo.git.diff(base_ref, head_ref, name_only=True).split('\n')

    # Initialize an empty dictionary to store file contents
    files = {}
    for file_path in diffs:
        try:
            # Fetch each file's content and store it in the files dictionary
            files[file_path] = get_file_content('./repo/' + file_path)
        except Exception as e:
            print(f"Failed to read {file_path}: {e}")

    return files

def send_to_openai(files):
    """
    This function sends the changed files to OpenAI for review.

    Args:
        files (dict): A dictionary containing the file paths as keys and their content as values.

    Returns:
        str: The review returned by OpenAI.
    """
    # Concatenate all the files into a single string
    code = '\n'.join(files.values())

    # Split the code into chunks that are each within the token limit
    chunks = textwrap.wrap(code, TOKEN_LIMIT)

    reviews = []
    for chunk in chunks:
        # Send a message to OpenAI with each chunk of the code for review
        message = openai.ChatCompletion.create(
            model="gpt-4.0",
            messages=[
                {
                    "role": "user",
                    "content": "You are assigned as a code reviewer. Your responsibility is to review the provided code and offer recommendations for enhancement. Identify any problematic code snippets, highlight potential issues, and evaluate the overall quality of the code you review:\n" + chunk
                }
            ],
        )

        # Add the assistant's reply to the list of reviews
        reviews.append(message['choices'][0]['message']['content'])

    # Join all the reviews into a single string
    review = "\n".join(reviews)

    return review

def post_comment(pr, comment):
    """
    This function posts a comment on the pull request with the review.

    Args:
        pr (PullRequest): The pull request object.
        comment (str): The comment to post.
    """
    # Post the OpenAI's response as a comment on the PR
    pr.create_issue_comment(comment)

def main():
    """
    The main function orchestrates the operations of:
    1. Fetching changed files from a PR
    2. Sending those files to OpenAI for review
    3. Posting the review as a comment on the PR
    """
    # Get the pull request event JSON
    with open(os.getenv('GITHUB_EVENT_PATH')) as json_file:
        event = json.load(json_file)
    
    # Instantiate the Github object using the Github token
    # and get the pull request object
    pr = Github(os.getenv('GITHUB_TOKEN')).get_repo(event['repository']['full_name']).get_pull(event['number'])

    # Get the changed files in the pull request
    files = get_changed_files(pr)

    # Send the files to OpenAI for review
    review = send_to_openai(files)

    # Post the review as a comment on the pull request
    post_comment(pr, review)

if __name__ == "__main__":
    main()  # Execute the main function