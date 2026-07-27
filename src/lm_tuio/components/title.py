from textual.widgets import Static

logo: str = r"""
   __   __  ___  ________  __________ 
  / /  /  |/  / /_  __/ / / /  _/ __ \
 / /__/ /|_/ /   / / / /_/ // // /_/ /
/____/_/  /_/   /_/  \____/___/\____/ 

------ LM Studio Dashboard ------  
"""


class Title(Static):
    '''Logo wigdet for primary dashboard.'''
    def on_mount(self) -> None:
        self.update(logo)
