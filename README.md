# Requirements:
- Given a starting URL, the crawler should visit each URL it finds on the same domain.
- It should print each URL visited, and a list of links found on that page.
- The crawler should be limited to one subdomain - so when you start with *https://crawlme.monzo.com/*, it would crawl all pages on the crawlme.monzo.com website, but not follow external links,

- Needs to handle recursive links.
- Needs tests
- Should optimize for concurrency.
- Should be efficient.
- Should have throttling.
- Should consider retries and timeouts.
- How will the site handle JS?
- Storage? Output format? In memory JSON?
- Trigger (manually vs live incremental updates)
- URL normalization
- Observability stack (logging)

Fetching -> Parsing -> Normalization -> Storing

TODO:
- implement multithreading
- implement retry logic
 - account for only trying up to X times and not giving job back to jobpool
- implement json output
- metrics?


# Tools
python3
Poetry (package management)

# Installation
## From source:
poetry run python main.py --debug "https://crawlme.monzo.com/"

## CLI Installation:
cd SuperCrawler/
python3 -m venv .venv-cli-test
source ./.venv-cli-test/bin/activate
pip install .
supercrawler https://example.com
