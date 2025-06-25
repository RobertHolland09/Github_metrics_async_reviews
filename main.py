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
    return pagination(github_repo_list_endpoint.format(owner=org))

def calculate_workflow_pass_rate(repo, workflow_name):
    workflow_id = get_repo_workflow_id(repo, workflow_name)
    if not workflow_id:
        return None

    try:
        json = call_url_get_json(github_actions_details.format(owner="zepz-engineering", repo=repo, workflow_id=workflow_id),headers)
    except requests.exceptions.RequestException as e:
        print("Error fetching worfklow details for {repo}, workflow ID {workflow_id}: {e}")
        return None
    
    total_count = 100
    workflow_success = 0

    workflow_runs = json.get('workflow_runs', [])
    total_count = len(workflow_runs)

    if total_count == 0:
        return 0.0 # No runs, so 0% success rate

    for i in json['workflow_runs']:
        if i['conclusion'] == "success":
            workflow_success += 1
    workflow_pass_rate = 100*(workflow_success/total_count)
    return workflow_pass_rate

def main():
    repo_list = get_repo_list("Zepz-Engineering")
    if not repo_list:
        print("No repositories found or an error accured while fetching.")
        return
    print(f"\nProcessing {len(repo_list)} repositories...")

    repo_success_rates = []

    print("\n---CodeQL Results---")
    # calculating CodeQL pass rates
    for repo in repo_list:
        codeql_pass_rates = calculate_workflow_pass_rate(repo, "CodeQL")
        if codeql_pass_rates is not None: # only adds if the calculation was successful
            repo_success_rates.append({"repository_name": repo, "success_rate": codeql_pass_rates})
            print(f"Repository: {repo}, CodeQL Success Rate: {codeql_pass_rates}%")
        else:
            repo_success_rates.append({"repository_name": repo, "success_rate": "No result"})
            print(f"Repository: {repo}, CodeQL Success Rate: No result")
    
    print("\n--Dependabot Results--")
    # Calculating Dependabot pass rates
    for repo in  repo_list:
        dependabot_pass_rates = calculate_workflow_pass_rate(repo, "Dependency review")
        if dependabot_pass_rates is not None: #only adds if the caluclation was successful
            repo_success_rates.append({"repository_name": repo, "success_rate": dependabot_pass_rates})
            print(f"Repository: {repo}, Dependabot Success Rate: {dependabot_pass_rates}%")
        else:
            repo_success_rates.append({"repository_name": repo, "success_rate": "No result"})
            print(f"Repository: {repo}, Dependabot Success Rate: No result")

if __name__ == "__main__":
    main()
