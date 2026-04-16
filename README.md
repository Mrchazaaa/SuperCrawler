# SuperCrawler
This project crawls a starting URL and recursively discovers pages linked within the same subdomain.

https://github.com/Mrchazaaa/SuperCrawler

# Usage

## CLI Installation:
```bash
cd supercrawler/
python3 -m venv .venv-cli
source ./.venv-cli/bin/activate
pip install .
supercrawler "https://crawlme.monzo.com"
```

Optional arguments:
```bash
supercrawler --max-concurrency=10 "https://crawlme.monzo.com" > ./output.json
supercrawler --log-level=INFO "https://crawlme.monzo.com" > ./output.json
supercrawler --persist-logs "https://crawlme.monzo.com" > ./output.json
```


## Module Import:
```bash
cd supercrawler/
poetry install
poetry run python
```

Synchronous example:
```python
from supercrawler import explore_domain
results = explore_domain("https://crawlme.monzo.com")
```

Asynchronous example:
```python
import asyncio
from supercrawler import explore_domain_async

results = asyncio.run(explore_domain_async("https://crawlme.monzo.com"))
```


## From source:
```bash
cd supercrawler/
poetry run python main.py "https://crawlme.monzo.com/"
```

Optional arguments:
```bash
poetry run python main.py --max-concurrency=10 "https://crawlme.monzo.com" > ./output.json
poetry run python main.py --log-level=INFO "https://crawlme.monzo.com" > ./output.json
poetry run python main.py --persist-logs "https://crawlme.monzo.com" > ./output.json
```
