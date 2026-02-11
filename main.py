import tkinter as tk

from ui import SecureArchiverUI
from archive_builder import ArchiveBuilder


def main() -> None:
    root = tk.Tk()
    root.title("SecureArchiver")
    root.minsize(480, 420)

    builder = ArchiveBuilder()
    SecureArchiverUI(root, builder)

    root.mainloop()


if __name__ == "__main__":
    main()