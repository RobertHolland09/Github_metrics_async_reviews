import requests
import logging
import os
import json

token = "placeholder"
headers = {"Authorization": "Bearer {}".format(token)}

# Endpoints used for collecting data for GH Actions.
github_actions_endpoint_run = "https://api.github.com/repos/{owner}/{repo}/actions/runs"

github_actions_details = "https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs?per_page=999" 

github_repo_list_endpoint = "https://api.github.com/orgs/{owner}/repos?per_page=100&page={page}"
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

        full_url = github_repo_list_endpoint.format(owner="zepz-engineering", page=page)
        response = requests.get(full_url, params=params, headers=headers) # was this the right idea to do for the response that you described?

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
    

# print(repo_array_list)

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