import requests
import os
import json

token = "Placeholder"
headers = {"Authorization": "Bearer {}".format(token)}

# Endpoints used for collecting data for GH Actions.
github_actions_endpoint_run = "https://api.github.com/repos/{owner}/{repo}/actions/runs"

github_repo_list_endpoint = "https://api.github.com/orgs/{owner}/repos?per_page=999"

def call_url_get_json(url, headers):
    response = requests.get(url, headers=headers)
    return response.json()

def get_repo_workflow_id(repo, workflow_name):
    json = call_url_get_json(github_actions_endpoint_run.format(owner= "zepz-engineering", repo=repo), headers)
    for i in json["workflow_runs"]:
        if i["name"] == workflow_name:
            return i["workflow_id"]
        
def get_repo_list():
    response = requests.get(github_repo_list_endpoint.format(owner="zepz-engineering"),headers=headers)
    data = response.json()
    return data

repo_list = get_repo_list()
if repo_list:
    print(f"Successfully retrieved {len(repo_list)} repositories:")
    with open("repo_list.txt", "a") as f:
        f.seek(0)
        f.truncate()
    for repo in repo_list:
        with open("repo_list.txt", "a") as f:
            f.write(f"- {repo.get('name')}\n")
        print(f"- {repo.get('name')}")
    else:
        print("Either no repo's were found or an error occured")


github_actions_details = "https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs?per_page=999" 


def calculate_workflow_pass_rate(repo, workflow_name):
    workflow_id = get_repo_workflow_id(repo, workflow_name)
    print(workflow_id)
    json = call_url_get_json(github_actions_details.format(owner="zepz-engineering", repo=repo, workflow_id=workflow_id),headers)
    total_count = 100
    workflow_success = 0
    for i in json['workflow_runs']:
        if i['conclusion'] == "success":
            workflow_success += 1
    workflow_pass_rate = 100*(workflow_success/total_count)
    return workflow_pass_rate

security_repo_Depebdabot = calculate_workflow_pass_rate("security", "Dependency review")
print("Security Repo Dependabot success rate: "+ str(security_repo_Depebdabot))

sw_backend_repo_CodeQL = calculate_workflow_pass_rate("sw-backend", "CodeQL")
print("sw-backend Repo CodeQL success rate: "+ str(sw_backend_repo_CodeQL))