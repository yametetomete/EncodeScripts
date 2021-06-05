import os

from typing import Union


class Config():
    desc: str
    title: str
    title_long: str
    resolution: int
    datapath: str

    def __init__(self, desc: Union[int, str], title: str, title_long: str, resolution: int, datapath: str) -> None:
        self.desc = desc if isinstance(desc, str) else f"{desc:02d}"
        self.title = title
        self.title_long = title_long
        self.resolution = resolution
        self.datapath = datapath

    def format_filename(self, filename: str) -> str:
        fname = filename.format(epnum=self.desc, title=self.title,
                                title_long=self.title_long, resolution=self.resolution)
        return os.path.join(f"../{self.desc}/", fname)
