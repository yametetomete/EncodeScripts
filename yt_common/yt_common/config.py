class Config():
    epnum: int
    title: str
    title_long: str
    resolution: int
    datapath: str

    def __init__(self, epnum: int, title: str, title_long: str, resolution: int, datapath: str) -> None:
        self.epnum = epnum
        self.title = title
        self.title_long = title_long
        self.resolution = resolution
        self.datapath = datapath

    def format_filename(self, filename: str) -> str:
        return filename.format(epnum=self.epnum, title=self.title,
                               title_long=self.title_long, resolution=self.resolution)
