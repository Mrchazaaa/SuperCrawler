from supercrawler.model.page_content import PageContent
from supercrawler.model.page_id import PageId


class Page:
    id: PageId
    url: str
    content: PageContent

    def __init__(self, id: PageId, url: str, content: PageContent):
        self.id = id
        self.url = url
        self.content = content