import requests

AUTH = ("aaranjany@qnovocorp.com", "wXuRu9rVqDcm.Evd7bf0-M94eamebBrsZZ/Z07zeb")


HOST = "https://qnovocorp.testrail.io"
BASE_URL = f"{HOST}/index.php?/api/v2"
HEADERS = {"Content-Type": "application/json"}
RUN_ID = 1366
STATUS_ID = 1  # 1 = Passed, 2 = Blocked, 4 = Retest, 5 = Failed

# 1. Fetch all Untested tests (status_id=3) in Run 1366
test_ids = []
url = f"{BASE_URL}/get_tests/{RUN_ID}&status_id=3"

while url:
    resp = requests.get(url, auth=AUTH, headers=HEADERS)
    if not resp.ok:
        print(f"HTTP {resp.status_code}: {resp.text[:500]}")
        resp.raise_for_status()
    res = resp.json()
    test_ids.extend(t["id"] for t in res["tests"])

    next_link = res.get("_links", {}).get("next")
    if next_link:
        # TestRail's _links['next'] already starts with '/api/v2/...'
        url = f"{HOST}/index.php?{next_link}" if not next_link.startswith("http") else next_link
    else:
        url = None

print(f"Found {len(test_ids)} untested tests. Updating...")

# 2. Bulk-update in batches of 1,000
for i in range(0, len(test_ids), 1000):
    batch = [{"test_id": tid, "status_id": STATUS_ID, "comment": "Bulk updated"} for tid in test_ids[i:i + 1000]]
    r = requests.post(f"{BASE_URL}/add_results/{RUN_ID}", auth=AUTH, headers=HEADERS, json={"results": batch})
    if not r.ok:
        print(f"HTTP {r.status_code}: {r.text[:500]}")
        r.raise_for_status()
    print(f"Updated {min(i + 1000, len(test_ids))}/{len(test_ids)}")

print("Done!")
