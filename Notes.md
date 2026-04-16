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
- retry logic

# Tools
python3
Poetry (package management)

