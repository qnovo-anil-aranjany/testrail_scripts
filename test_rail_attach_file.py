import requests
from concurrent.futures import ThreadPoolExecutor
import time


AUTH = ("aaranjany@qnovocorp.com", "")


HOST = "https://qnovocorp.testrail.io"
BASE_URL = f"{HOST}/index.php?/api/v2"
HEADERS = {"Content-Type": "application/json"}
RUN_ID = 1366
STATUS_ID = 1  # 1 = Passed, 2 = Blocked, 4 = Retest, 5 = Failed

FILE_PATH = r"C:\Users\aaranjany\OneDrive - Qnovo, Inc\Pictures\Screenshots\test_2.png"

session = requests.Session()
session.auth = AUTH

# 1. Fetch all Passed results (status_id=1) in Run 1366 and keep the latest result_id per test
latest_result_by_test = {}
url = f"{BASE_URL}/get_results_for_run/{RUN_ID}&status_id=1"

while url:
    resp = session.get(url, headers={"Content-Type": "application/json"})
    resp.raise_for_status()
    res = resp.json()
    for r in res["results"]:
        tid = r["test_id"]
        # Results are returned newest-first, so keep the first one seen per test_id
        if tid not in latest_result_by_test:
            latest_result_by_test[tid] = r["id"]

    next_link = res.get("_links", {}).get("next")
    url = (f"{HOST}/index.php?{next_link}" if not next_link.startswith("http") else next_link) if next_link else None

result_ids = list(latest_result_by_test.values())
print(f"Found {len(result_ids)} Passed test results to attach file to.")

# 2. Load test_2.png once into memory
with open(FILE_PATH, "rb") as f:
    file_bytes = f.read()


# 3. Upload attachment to each existing result_id with automatic 429 rate-limit retry
def attach_file(result_id):
    while True:
        r = session.post(
            f"{BASE_URL}/add_attachment_to_result/{result_id}",
            files={"attachment": ("test_2.png", file_bytes, "image/png")}
        )
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 5))
            time.sleep(wait)
            continue
        r.raise_for_status()
        return


print("Uploading test_2.png...")
with ThreadPoolExecutor(max_workers=4) as executor:
    for idx, _ in enumerate(executor.map(attach_file, result_ids), 1):
        if idx % 250 == 0 or idx == len(result_ids):
            print(f"Attached: {idx}/{len(result_ids)}")

print("Done! All attachments uploaded.")
