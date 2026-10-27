"""Manual API test against the running Docker container.

Uses only the Python standard library, so no extra packages are needed.

Usage:
    python scripts/smoke_test.py              # test the running API
    python scripts/smoke_test.py --recreate   # also remove + recreate the container
                                              # and check the data is still there
"""

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request

BASE_URL = "http://localhost:8000"
CONTAINER = "student-api"
IMAGE = "student-records-api:1.0"
VOLUME = "student-data"

results = []


def request(method, path, body=None):
    """Send an HTTP request and return (status_code, json_body)."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE_URL + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read())


def check(name, expected, actual, passed):
    results.append((name, expected, actual, passed))
    print(f"[{'PASS' if passed else 'FAIL'}] {name}\n       expected: {expected}\n       actual:   {actual}")


def wait_for_api(seconds=30):
    for _ in range(seconds):
        try:
            if request("GET", "/health")[0] == 200:
                return True
        except (urllib.error.URLError, ConnectionError):
            pass
        time.sleep(1)
    return False


def run(cmd):
    print(f"  $ {' '.join(cmd)}")
    subprocess.run(cmd, check=True, capture_output=True)


def main():
    if not wait_for_api(5):
        print("API is not reachable on", BASE_URL, "- is the container running?")
        sys.exit(1)

    roll_no = f"T{int(time.time()) % 100000}"
    student = {"name": "Test Student", "roll_no": roll_no,
               "department": "Computer Engineering", "email": "test.student@example.com"}

    status, body = request("GET", "/health")
    check("Health check", "200 {'status': 'ok'}", f"{status} {body}", status == 200 and body == {"status": "ok"})

    status, body = request("POST", "/students", student)
    new_id = body.get("id")
    check("Add a student (POST /students)", "201 with new id", f"{status} id={new_id}", status == 201 and new_id)

    status, body = request("GET", "/students")
    found = any(s["id"] == new_id for s in body)
    check("View all students (GET /students)", "200, list contains new student",
          f"{status}, {len(body)} students, new student found={found}", status == 200 and found)

    status, body = request("GET", f"/students/{new_id}")
    check("View student by ID", f"200 roll_no={roll_no}", f"{status} roll_no={body.get('roll_no')}",
          status == 200 and body.get("roll_no") == roll_no)

    updated = {**student, "department": "Information Technology"}
    status, body = request("PUT", f"/students/{new_id}", updated)
    check("Update student (PUT)", "200 department=Information Technology",
          f"{status} department={body.get('department')}",
          status == 200 and body.get("department") == "Information Technology")

    status, _ = request("POST", "/students", {**student, "roll_no": "BAD1", "email": "not-an-email"})
    check("Invalid input: bad email", "422", status, status == 422)

    status, _ = request("POST", "/students", {"name": "Only Name"})
    check("Invalid input: missing fields", "422", status, status == 422)

    status, body = request("GET", "/students/99999")
    check("Non-existent student ID (GET)", "404", f"{status} {body.get('detail')}", status == 404)

    status, _ = request("PUT", "/students/99999", student)
    check("Non-existent student ID (PUT)", "404", status, status == 404)

    status, _ = request("POST", "/students", student)
    check("Duplicate roll number", "409", status, status == 409)

    if "--recreate" in sys.argv:
        print("\nRecreating the container...")
        run(["docker", "rm", "-f", CONTAINER])
        run(["docker", "run", "-d", "--name", CONTAINER, "-p", "8000:8000",
             "-v", f"{VOLUME}:/app/data", IMAGE])
        up = wait_for_api(30)
        check("API reachable after container recreation", "200 on /health", "200" if up else "not reachable", up)
        status, body = request("GET", f"/students/{new_id}")
        check("Data persists after recreation", "200 department=Information Technology",
              f"{status} department={body.get('department')}",
              status == 200 and body.get("department") == "Information Technology")

    passed = sum(1 for r in results if r[3])
    print(f"\n{passed}/{len(results)} checks passed")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
