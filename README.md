# GPU-performance-scripts
A set of scripts for testing GPU node performance. These scripts are not a complete replacement for QAA tests, it is more prioritised to run auto-tests.

The documentation of the test coverage - https://wiki.gcore.lu/display/GCLOUD2/AI+Infrastructure+Test+Acceptance+Server

Test cases - https://testrail.ad.gcore.lu/index.php?/suites/view/3&group_by=cases:section_id&group_id=744&group_order=asc&display_deleted_cases=0

## 📦 Content

- `scripts/` — scripts for running tests
- `requirements.txt` — Python dependencies

## 🚀 Quick start

### 1. Clone a repository
```bash
git clone https://gitlab-ed7.cloud.gc.onl/cloudapi/qa/team-qa.git
cd team-qa
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Running a test
```bash
python scripts/gpu_test.py

(replace gpu_test.py with the name of your main script)
```

## 📄 Licence and author
### Author: Manual QA team
### Company: Gcore
### Licence: for internal use only!