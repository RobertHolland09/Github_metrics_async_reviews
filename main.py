import requests
import logging
import os
import json

token = "placeholder"
headers = {"Authorization": "Bearer {}".format(token)}

# Endpoints used for collecting data for GH Actions.
github_actions_endpoint_run = "https://api.github.com/repos/{owner}/{repo}/actions/runs"

github_actions_details = "https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs?per_page=999" 

github_repo_list_endpoint = "https://api.github.com/orgs/{owner}/repos"

github_workflows_endpoint = "https://api.github.com/repos/{owner}/{repo}/actions/workflows"
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

def get_repo_workflow_details(owner, repo):
    workflows_url = github_workflows_endpoint.format(owner=owner, repo=repo)
    workflows_data = call_url_get_json(workflows_url, headers)
    if workflows_data and "workflows" in workflows_data:
        return workflows_data["workflows"]
    return []

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
    repo_codeql_status = []
    repo_dependabot_status = []

    print("\n---CodeQL Results---")
    # calculating CodeQL pass rates
    for repo in repo_list:
        print(f"Checking {repo} for CodeQL workflow from codeql.yaml...")
        
        found_codeql_workflow = False
        workflow_details_list = get_repo_workflow_details("Zepz-Engineering", repo)

        if workflow_details_list:
            for workflow in workflow_details_list:
                # Check if the workflow name contains "CodeQL" AND its path ends with "codeql.yaml"
                path = workflow["path"].split("/")[-1]
                if "codeql" in workflow["name"].lower() and (path == "codeql.yml" or path == "codeql.yaml"):
                    codeql_workflow_id = workflow["id"]
                    codeql_workflow_name = workflow["name"]
                    
                    codeql_pass_rates = calculate_workflow_pass_rate(repo, codeql_workflow_id)
                    if codeql_pass_rates is not None:
                        repo_codeql_status.append({"repository_name": repo, "codeql_workflow_name": codeql_workflow_name, "success_rate": codeql_pass_rates, "source_file": workflow["path"]})
                        print(f"Repository: {repo}, CodeQL Workflow: '{codeql_workflow_name}', Source File: {workflow['path']}, Success Rate: {codeql_pass_rates}%")
                    else:
                        repo_codeql_status.append({"repository_name": repo, "codeql_workflow_name": codeql_workflow_name, "success_rate": "Calculation Failed", "source_file": workflow["path"]})
                        print(f"Repository: {repo}, CodeQL Workflow: '{codeql_workflow_name}', Source File: {workflow['path']}, Success Rate: Calculation Failed")
                    
                    found_codeql_workflow = True
                    break # Found the specific CodeQL workflow, no need to check other workflows in this repo
        
        if not found_codeql_workflow:
            repo_codeql_status.append({"repository_name": repo, "codeql_workflow_name": "Not Found (from codeql.yaml)", "success_rate": "Not Applicable", "source_file": "N/A"})
            print(f"Repository: {repo}, CodeQL Status: No CodeQL workflow found originating from 'codeql.yaml'.")
    
    print("\n--Dependabot Results--")
    # Calculating Dependabot pass rates
    for repo in  repo_list:
        print(f"Checking {repo} for Dependabot workflow from workflows...")
        
        found_dependabot_workflow = False
        workflow_details_list = get_repo_workflow_details("Zepz-Engineering", repo)

        if workflow_details_list:
            for workflow in workflow_details_list:
                path = workflow["path"].split("/")[-1]
                if "Dependency review" in workflow["name"].lower() and (path == "depedendabot.yml" or path == "gradle-depsubmission-review.yaml" or path == "dependabot.yaml" or path == "gradle-depsubmission-review.yml"):
                    dependabot_workflow_id = workflow["id"]
                    depednabot_workflow_name = workflow["name"]
                    
                    dependabot_pass_rates = calculate_workflow_pass_rate(repo, dependabot_workflow_id)
                    if dependabot_pass_rates is not None:
                        repo_dependabot_status.append({"repository_name": repo, "dependabot_workflow_name": depednabot_workflow_name, "success_rate": dependabot_pass_rates, "source_file": workflow["path"]})
                        print(f"Repository: {repo}, Dependabot Workflow: '{depednabot_workflow_name}', Source File: {workflow['path']}, Success Rate: {dependabot_pass_rates}%")
                    else:
                        repo_dependabot_status.append({"repository_name": repo, "dependabot_workflow_name": depednabot_workflow_name, "success_rate": "Calculation Failed", "source_file": workflow["path"]})
                        print(f"Repository: {repo}, Dependabot Workflow: '{depednabot_workflow_name}', Source File: {workflow['path']}, Success Rate: Calculation Failed")
                    
                    found_dependabot_workflow = True
                    break # Found the specific Dependabot workflow, no need to check other workflows in this repo
        
        if not found_dependabot_workflow:
            repo_dependabot_status.append({"repository_name": repo, "dependabot_workflow_name": "Not Found (from dependabot.yml/gradle-depsubmission-review.yml)", "success_rate": "Not Applicable", "source_file": "N/A"})
            print(f"Repository: {repo}, Dependabot Status: No Dependabot workflow found originating from 'dependabot.yml' or 'gradle-depsubmission-review.yml'.")

if __name__ == "__main__":
    main()
