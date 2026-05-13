import tkinter as tk
from ui.app_ui import FantasyDraftApp


def main():
    root = tk.Tk()
    app = FantasyDraftApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
    