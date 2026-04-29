from pathlib import Path

from constants import LAST_PROXY_FILE, PROXIES_FILE


class ProxyManager:
    def __init__(self):

        if PROXIES_FILE.exists():
            with open(PROXIES_FILE, "r") as file:
                self._proxies: list[str] = file.readlines()
        else:
            self._proxies = []

        if LAST_PROXY_FILE.exists():
            with open(LAST_PROXY_FILE, "r") as file:
                self._current_index: int = int(file.read())
        else:
            self._current_index = 0

    def get_current_proxy(self) -> str | None:
        if self._proxies:
            return self._proxies[self._current_index]
        return None

    def next_proxy(self):
        if  self._proxies:
            self._current_index = (self._current_index + 1) % len(self._proxies)
            self._save_last_used()


    def _save_last_used(self):
        with open(LAST_PROXY_FILE, "w") as file:
            file.write(str(self._current_index))
