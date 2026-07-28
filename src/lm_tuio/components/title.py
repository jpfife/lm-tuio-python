"""Logo display and title widget for primary dashboard screen."""

from textual.widgets import Static

logo: str = r"""
   __   __  ___  ________  __________ 
  / /  /  |/  / /_  __/ / / /  _/ __ \
 / /__/ /|_/ /   / / / /_/ // // /_/ /
/____/_/  /_/   /_/  \____/___/\____/ 

"""


class Title(Static):
    """Logo wigdet for primary dashboard."""

    def on_mount(self) -> None:
        self.update(logo)
