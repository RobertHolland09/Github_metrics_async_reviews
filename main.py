import requests
import logging
import os
import json

token = "Placeholder"
headers = {"Authorization": "Bearer {}".format(token)}

# Endpoints used for collecting data for GH Actions.
github_actions_endpoint_run = "https://api.github.com/repos/{owner}/{repo}/actions/runs"

github_actions_details = "https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs?per_page=999" 

github_repo_list_endpoint = "https://api.github.com/orgs/{owner}/repos"
# End of Endpoints 

def call_url_get_json(url, headers):
    response = requests.get(url, headers=headers)
    return response.json()

def get_repo_workflow_id(repo, workflow_name):
    json = call_url_get_json(github_actions_endpoint_run.format(owner= "zepz-engineering", repo=repo), headers)
    for i in json["workflow_runs"]:
        if i["name"] == workflow_name:
            return i["workflow_id"]
        
def pagination(url):
        
    page = 1
    per_page = 100
    results = []

    while True:        
        params = {
            'page': page,
            'per_page': per_page
        }

        response = requests.get(url, params=params, headers=headers)

        if response.status_code == 200:
            res = response.json()
            for r in res:
                repo_name = r.get('name')
                if repo_name:
                    results.append(r.get('name')) 

            if len(res) < per_page:
                break  # Reached the last page, exit the loop

            page += 1
        else:
            logging.error('Request failed with: ' + str(response.status_code))
            return None
    print(results) 
    return results
    
def get_repo_list(org):
    return pagination(github_repo_list_endpoint.format(org))

def calculate_workflow_pass_rate(repo, workflow_name):
    workflow_id = get_repo_workflow_id(repo, workflow_name)
    if not workflow_id:
        print("could not find workflow ID for '{workflow_name}' in repository '{repo}'. Skipping")
        return None

    print(f"Workflow ID for {repo}, {workflow_name}: {workflow_id}")
    try:
        json = call_url_get_json(github_actions_details.format(owner="zepz-engineering", repo=repo, workflow_id=workflow_id),headers)
    except requests.exceptions.RequestException as e:
        print("Error fetching worfklow details for {repo}, workflow ID {workflow_id}: {e}")
        return None
    
    total_count = 100
    workflow_success = 0

    for i in json['workflow_runs']:
        if i['conclusion'] == "success":
            workflow_success += 1
    workflow_pass_rate = 100*(workflow_success/total_count)
    return workflow_pass_rate

def main():
    repo_list = get_repo_list("Zepz-Engineering")
    print(repo_list)

security_repo_Depebdabot = calculate_workflow_pass_rate("security", "Dependency review")
print("Security Repo Dependabot success rate: "+ str(security_repo_Depebdabot))

sw_backend_repo_CodeQL = calculate_workflow_pass_rate("sw-backend", "CodeQL")
print("sw-backend Repo CodeQL success rate: "+ str(sw_backend_repo_CodeQL))