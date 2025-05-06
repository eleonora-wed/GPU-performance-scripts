import re
from pathlib import Path

def extract_results(file_path):
    pattern = re.compile(r"\[SUM\]\s+[\d.\-]+\s+sec\s+([\d.]+)\s+GBytes\s+([\d.,]+)\s+Gbits/sec\s+(\d+)\s+sender")

    with open(file_path, 'r') as f:
        lines = f.readlines()

    for line in reversed(lines):
        match = pattern.search(line)
        if match:
            transfer = float(match.group(1))
            bitrate = float(match.group(2).replace(',', '.'))
            retrans = int(match.group(3))
            return {
                "transfer": transfer,
                "bitrate": bitrate,
                "retrans": retrans
            }

def main():
    files_5201 = sorted(Path('.').glob('*5201.txt'))
    files_5202 = sorted(Path('.').glob('*5202.txt'))

    # Пройти по парам (5201.txt и 5202.txt)
    for f1, f2 in zip(files_5201, files_5202):
        stats_5201 = extract_results(f1)
        stats_5202 = extract_results(f2)

        total_bitrate = round(stats_5201["bitrate"] + stats_5202["bitrate"], 2)

        print(f"File: {f1.name}")
        print(f"  Transfer : {stats_5201['transfer']} GBytes")
        print(f"  Bitrate  : {stats_5201['bitrate']} Gbits/sec")
        print(f"  Retr     : {stats_5201['retrans']}\n")

        print(f"File: {f2.name}")
        print(f"  Transfer : {stats_5202['transfer']} GBytes")
        print(f"  Bitrate  : {stats_5202['bitrate']} Gbits/sec")
        print(f"  Retr     : {stats_5202['retrans']}\n")

        print(f"Total bitrate: {total_bitrate} Gbits/sec\n{'-' * 40}\n")

if __name__ == "__main__":
    main()