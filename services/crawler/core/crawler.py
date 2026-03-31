
# Base abstract class for all crawlers
class Clawler:
    def __init__(self, name, output_dir, base_url=None):
        self.name = name
        self.output_dir = output_dir
        self.base_url = base_url

    def crawl(self):
        raise NotImplementedError("Subclasses must implement this method")