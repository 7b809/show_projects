import requests, os
from dotenv import load_dotenv

load_dotenv()

RAILWAY_TOKEN = os.getenv("RAILWAY_TOKEN")

url = "https://backboard.railway.com/graphql/v2"

headers = {
    "Authorization": f"Bearer {RAILWAY_TOKEN}",
    "Content-Type": "application/json"
}

query = """
query {
  me {
    workspaces {
      name
      projects {
        edges {
          node {
            id
            name
            createdAt
            services {
              edges {
                node {
                  id
                  name
                  createdAt
                }
              }
            }
          }
        }
      }
    }
  }
}
"""

response = requests.post(url, headers=headers, json={"query": query})
data = response.json()

print("FULL RESPONSE:\n", data)

print("\nPROJECT STRUCTURE:\n")

try:
    workspaces = data["data"]["me"]["workspaces"]

    for ws in workspaces:

        print("Workspace:", ws["name"])

        for p in ws["projects"]["edges"]:

            project = p["node"]

            print("\nProject:", project["name"])
            print("Created:", project["createdAt"])

            services = project["services"]["edges"]

            if services:
                print("Services:")
                for s in services:
                    service = s["node"]
                    print("   -", service["name"])
            else:
                print("   No services")

            print("------------------------")

except Exception as e:
    print("Error:", e)