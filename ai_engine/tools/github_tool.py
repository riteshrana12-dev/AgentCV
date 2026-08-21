import httpx , asyncio , requests , base64
from typing import List, Dict, Any

async def fetch_github_user_repos( max_repos: int =10)-> List[Dict[str,Any]]:


    url = f"https://api.github.com/users/riteshrana12-dev/repos?sort=updated&per_page={max_repos}"
    headers = {"user-Agent": "AI-Resume-Analyzer"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers=headers)
        
        if response.status_code == 404:
            return []
        
        response.raise_for_status()
        repos = response.json()

    repo_list = []
    for repo in repos:
        # Ignore forks to focus on user's original work
        if repo.get("fork"):
            continue

        readme = fetch_repo_readme(repo.get("name"))

        repo_list.append({
            "name": repo.get("name"),
            "description": repo.get("description") or "No description provided.",
            "language": repo.get("language") or "Not specified",
            "stars": repo.get("stargazers_count", 0),
            "url": repo.get("html_url"),
            "topics": repo.get("topics", []),
            "readme":readme
        })

    print("repo_list: ",repo_list)
    # return repo_list


def fetch_repo_readme(repo):
    url = f"https://api.github.com/repos/riteshrana12-dev/{repo}/readme"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        content = base64.b64decode(data['content']).decode('utf-8')
        return content
    else:
        return f"Could not fetch README: {response.status_code}"





async def main():
    await fetch_github_user_repos()

if __name__ == "__main__":
    asyncio.run(main())