## How to to use

### 1. Install FIO util
```bash
ansible-playbook -i ./inventory/inventory.ini ./playbooks/install_fio.yml
```
### 2. Run tests

```bash
ansible-playbook -i ./inventory/inventory.ini ./playbooks/run_tests.yml
```

### Parsing results

```bash
python parse_results.py --input-dir fio_results --output-file fio_summary.xlsx
```