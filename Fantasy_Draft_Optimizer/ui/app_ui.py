import tkinter as tk
from tkinter import ttk, messagebox

from logic.data_loader import load_master_data
from logic.ranking import calculate_vor


class FantasyDraftApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Fantasy Football Draft Optimizer")
        self.root.geometry("1660x880")
        self.root.configure(bg="#f3f4f6")

        self.original_df = None
        self.base_df = None
        self.available_df = None
        self.sort_reverse = {}

        self.search_var = tk.StringVar()
        self.position_filter = "ALL"
        self.league_format = "Full PPR"

        self.num_teams = 10
        self.total_rounds = 16
        self.team_names = [f"Team {i}" for i in range(1, self.num_teams + 1)]
        self.teams = {team: self.create_empty_roster() for team in self.team_names}

        self.current_pick_index = 0
        self.draft_order = self.generate_snake_draft_order()

        self.selected_team = tk.StringVar()

        self.tree = None
        self.roster_labels = {}
        self.team_dropdown = None

        self.round_label = None
        self.pick_label = None
        self.clock_label = None

        self.filter_buttons = {}
        self.recommendation_labels = []
        self.recent_picks_listbox = None
        self.draft_board_listbox = None

        self.setup_styles()
        self.setup_ui()
        self.load_original_player_data()
        self.start_new_draft()

    def create_empty_roster(self):
        return {
            "QB": None,
            "RB1": None,
            "RB2": None,
            "WR1": None,
            "WR2": None,
            "TE": None,
            "FLEX1": None,
            "FLEX2": None,
            "Bench1": None,
            "Bench2": None,
            "Bench3": None,
            "Bench4": None,
            "Bench5": None,
        }

    def generate_snake_draft_order(self):
        order = []
        for rnd in range(1, self.total_rounds + 1):
            if rnd % 2 == 1:
                round_order = self.team_names[:]
            else:
                round_order = self.team_names[::-1]
            order.extend(round_order)
        return order

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background="white",
            foreground="black",
            rowheight=28,
            fieldbackground="white",
            font=("Arial", 10)
        )
        style.configure(
            "Treeview.Heading",
            background="#1f3b73",
            foreground="white",
            font=("Arial", 10, "bold"),
            relief="flat"
        )
        style.map("Treeview.Heading", background=[("active", "#2f5aa8")])

        style.configure("Modern.TCombobox", padding=6, font=("Arial", 10))

    def setup_ui(self):
        header_frame = tk.Frame(self.root, bg="#1f3b73", height=70)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        header_text_frame = tk.Frame(header_frame, bg="#1f3b73")
        header_text_frame.pack(side="left", padx=20, pady=10)

        header_title = tk.Label(
            header_text_frame,
            text="Fantasy Football Draft Optimizer",
            bg="#1f3b73",
            fg="white",
            font=("Arial", 20, "bold")
        )
        header_title.pack(anchor="w")

        header_subtitle = tk.Label(
            header_text_frame,
            text=f"League Format: {self.league_format} | Teams: 10",
            bg="#1f3b73",
            fg="#dbeafe",
            font=("Arial", 10, "bold")
        )
        header_subtitle.pack(anchor="w")

        status_frame = tk.Frame(self.root, bg="#f3f4f6")
        status_frame.pack(fill="x", padx=15, pady=(12, 6))

        self.round_label = self.create_status_card(status_frame, "Round", "1")
        self.pick_label = self.create_status_card(status_frame, "Pick", "1")
        self.clock_label = self.create_status_card(status_frame, "Team on Clock", "Team 1", width=260)

        controls_frame = tk.Frame(self.root, bg="#f3f4f6")
        controls_frame.pack(fill="x", padx=15, pady=8)

        controls_card = tk.Frame(controls_frame, bg="white", bd=1, relief="solid")
        controls_card.pack(fill="x")

        controls_inner = tk.Frame(controls_card, bg="white")
        controls_inner.pack(fill="x", padx=12, pady=12)

        new_draft_button = tk.Button(
            controls_inner,
            text="Start New Draft",
            command=self.start_new_draft,
            bg="#10b981",
            fg="white",
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=14,
            pady=8,
            cursor="hand2"
        )
        new_draft_button.pack(side="left", padx=6)

        tk.Label(
            controls_inner,
            text="Viewing Team:",
            bg="white",
            fg="#111827",
            font=("Arial", 11, "bold")
        ).pack(side="left", padx=(20, 8))

        self.team_dropdown = ttk.Combobox(
            controls_inner,
            textvariable=self.selected_team,
            values=self.team_names,
            state="readonly",
            width=16,
            style="Modern.TCombobox"
        )
        self.team_dropdown.pack(side="left", padx=6)
        self.team_dropdown.bind("<<ComboboxSelected>>", self.on_team_change)

        prev_button = tk.Button(
            controls_inner,
            text="Previous Team",
            command=self.go_to_previous_team,
            bg="#e5e7eb",
            fg="#111827",
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=14,
            pady=8,
            cursor="hand2"
        )
        prev_button.pack(side="left", padx=8)

        next_button = tk.Button(
            controls_inner,
            text="Next Team",
            command=self.go_to_next_team,
            bg="#e5e7eb",
            fg="#111827",
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=14,
            pady=8,
            cursor="hand2"
        )
        next_button.pack(side="left", padx=8)

        draft_button = tk.Button(
            controls_inner,
            text="Draft Selected Player",
            command=self.draft_selected_player,
            bg="#2563eb",
            fg="white",
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=16,
            pady=8,
            cursor="hand2"
        )
        draft_button.pack(side="right", padx=8)

        main_frame = tk.Frame(self.root, bg="#f3f4f6")
        main_frame.pack(fill="both", expand=True, padx=15, pady=(5, 15))

        left_panel = tk.Frame(main_frame, bg="white", bd=1, relief="solid")
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(
            left_panel,
            text="Available Players",
            bg="white",
            fg="#111827",
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=12, pady=(12, 6))

        search_filter_frame = tk.Frame(left_panel, bg="white")
        search_filter_frame.pack(fill="x", padx=12, pady=(0, 8))

        tk.Label(
            search_filter_frame,
            text="Search:",
            bg="white",
            fg="#111827",
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=(0, 6))

        search_entry = tk.Entry(
            search_filter_frame,
            textvariable=self.search_var,
            font=("Arial", 10),
            width=28
        )
        search_entry.pack(side="left", padx=(0, 12))
        search_entry.bind("<KeyRelease>", self.on_search_change)

        tk.Label(
            search_filter_frame,
            text="Filter:",
            bg="white",
            fg="#111827",
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=(0, 6))

        for pos in ["ALL", "QB", "RB", "WR", "TE"]:
            btn = tk.Button(
                search_filter_frame,
                text=pos,
                command=lambda p=pos: self.set_position_filter(p),
                bg="#2563eb" if pos == "ALL" else "#e5e7eb",
                fg="white" if pos == "ALL" else "#111827",
                font=("Arial", 9, "bold"),
                relief="flat",
                padx=10,
                pady=5,
                cursor="hand2"
            )
            btn.pack(side="left", padx=3)
            self.filter_buttons[pos] = btn

        table_frame = tk.Frame(left_panel, bg="white")
        table_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        columns = ("rank", "player_name", "team", "position", "player_projection", "adp", "vor")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=32)

        column_widths = {
            "rank": 70,
            "player_name": 220,
            "team": 90,
            "position": 90,
            "player_projection": 140,
            "adp": 90,
            "vor": 90,
        }

        for col in columns:
            self.sort_reverse[col] = False
            self.tree.heading(
                col,
                text=col.replace("_", " ").title(),
                command=lambda c=col: self.sort_treeview(c)
            )
            self.tree.column(col, width=column_widths[col], anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        right_wrapper = tk.Frame(main_frame, bg="#f3f4f6", width=430)
        right_wrapper.pack(side="right", fill="y")
        right_wrapper.pack_propagate(False)

        recommend_panel = tk.Frame(right_wrapper, bg="white", bd=1, relief="solid", height=220)
        recommend_panel.pack(fill="x", pady=(0, 10))
        recommend_panel.pack_propagate(False)

        tk.Label(
            recommend_panel,
            text="Top Recommendations",
            bg="white",
            fg="#111827",
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=12, pady=(12, 6))

        tk.Label(
            recommend_panel,
            text="Best available players for the current team in Full PPR",
            bg="white",
            fg="#6b7280",
            font=("Arial", 10)
        ).pack(anchor="w", padx=12, pady=(0, 10))

        recommend_body = tk.Frame(recommend_panel, bg="white")
        recommend_body.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        for _ in range(3):
            card = tk.Label(
                recommend_body,
                text="--",
                bg="#f9fafb",
                fg="#111827",
                font=("Arial", 10),
                justify="left",
                anchor="w",
                bd=1,
                relief="solid",
                padx=10,
                pady=8
            )
            card.pack(fill="x", pady=4)
            self.recommendation_labels.append(card)

        roster_panel = tk.Frame(right_wrapper, bg="white", bd=1, relief="solid", height=470)
        roster_panel.pack(fill="x", pady=(0, 10))
        roster_panel.pack_propagate(False)

        tk.Label(
            roster_panel,
            text="Team Roster",
            bg="white",
            fg="#111827",
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=12, pady=(12, 6))

        tk.Label(
            roster_panel,
            text="Current selected team's drafted players",
            bg="white",
            fg="#6b7280",
            font=("Arial", 10)
        ).pack(anchor="w", padx=12, pady=(0, 10))

        roster_frame = tk.Frame(roster_panel, bg="white")
        roster_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        for slot in self.create_empty_roster():
            slot_row = tk.Frame(roster_frame, bg="#f9fafb", bd=1, relief="solid")
            slot_row.pack(fill="x", pady=4)

            tk.Label(
                slot_row,
                text=slot,
                bg="#f9fafb",
                fg="#111827",
                font=("Arial", 10, "bold"),
                width=8,
                anchor="w"
            ).pack(side="left", padx=8, pady=8)

            player_label = tk.Label(
                slot_row,
                text="--",
                bg="#f9fafb",
                fg="#374151",
                font=("Arial", 10),
                anchor="w",
                justify="left",
                wraplength=260
            )
            player_label.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=8)

            self.roster_labels[slot] = player_label

        bottom_right = tk.Frame(right_wrapper, bg="#f3f4f6")
        bottom_right.pack(fill="both", expand=True)

        picks_panel = tk.Frame(bottom_right, bg="white", bd=1, relief="solid", height=220)
        picks_panel.pack(side="left", fill="both", expand=True, padx=(0, 5))
        picks_panel.pack_propagate(False)

        tk.Label(
            picks_panel,
            text="Recent Picks",
            bg="white",
            fg="#111827",
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=12, pady=(12, 6))

        tk.Label(
            picks_panel,
            text="Most recent drafted players",
            bg="white",
            fg="#6b7280",
            font=("Arial", 10)
        ).pack(anchor="w", padx=12, pady=(0, 10))

        self.recent_picks_listbox = tk.Listbox(
            picks_panel,
            font=("Arial", 10),
            bg="white",
            fg="black",
            bd=1,
            relief="solid",
            highlightthickness=0,
            height=10
        )
        self.recent_picks_listbox.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        board_panel = tk.Frame(bottom_right, bg="white", bd=1, relief="solid", height=220)
        board_panel.pack(side="right", fill="both", expand=True, padx=(5, 0))
        board_panel.pack_propagate(False)

        tk.Label(
            board_panel,
            text="Draft Board",
            bg="white",
            fg="#111827",
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=12, pady=(12, 6))

        tk.Label(
            board_panel,
            text="All draft picks in order",
            bg="white",
            fg="#6b7280",
            font=("Arial", 10)
        ).pack(anchor="w", padx=12, pady=(0, 10))

        self.draft_board_listbox = tk.Listbox(
            board_panel,
            font=("Arial", 10),
            bg="white",
            fg="black",
            bd=1,
            relief="solid",
            highlightthickness=0,
            height=10
        )
        self.draft_board_listbox.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def create_status_card(self, parent, title, value, width=150):
        card = tk.Frame(parent, bg="white", bd=1, relief="solid", width=width, height=65)
        card.pack(side="left", padx=6)
        card.pack_propagate(False)

        tk.Label(
            card,
            text=title,
            bg="white",
            fg="#6b7280",
            font=("Arial", 10, "bold")
        ).pack(anchor="w", padx=10, pady=(8, 0))

        value_label = tk.Label(
            card,
            text=value,
            bg="white",
            fg="#111827",
            font=("Arial", 12, "bold")
        )
        value_label.pack(anchor="w", padx=10, pady=(4, 0))
        return value_label

    def load_original_player_data(self):
        try:
            df = load_master_data("data/master_players.csv")
            ranked = calculate_vor(df)
            self.original_df = ranked.copy()
        except Exception as e:
            messagebox.showerror("Startup Error", str(e))

    def start_new_draft(self):
        if self.original_df is None:
            messagebox.showerror("Error", "Original player data could not be loaded.")
            return

        self.teams = {team: self.create_empty_roster() for team in self.team_names}
        self.current_pick_index = 0
        self.draft_order = self.generate_snake_draft_order()
        self.selected_team.set(self.team_names[0])

        self.base_df = self.original_df.copy()
        self.available_df = self.original_df.copy()

        self.position_filter = "ALL"
        self.search_var.set("")
        self.update_filter_button_styles()

        self.clear_listbox(self.recent_picks_listbox)
        self.clear_listbox(self.draft_board_listbox)

        self.apply_filters_and_refresh()
        self.update_draft_status()
        self.update_roster_display()
        self.update_recommendations()

    def clear_listbox(self, listbox):
        if listbox is not None:
            listbox.delete(0, tk.END)

    def on_search_change(self, event=None):
        self.apply_filters_and_refresh()

    def set_position_filter(self, position):
        self.position_filter = position
        self.update_filter_button_styles()
        self.apply_filters_and_refresh()

    def update_filter_button_styles(self):
        for pos, btn in self.filter_buttons.items():
            if pos == self.position_filter:
                btn.config(bg="#2563eb", fg="white")
            else:
                btn.config(bg="#e5e7eb", fg="#111827")

    def apply_filters_and_refresh(self):
        if self.base_df is None:
            return

        filtered = self.base_df.copy()

        search_text = self.search_var.get().strip().lower()
        if search_text:
            filtered = filtered[
                filtered["player_name"].astype(str).str.lower().str.contains(search_text, na=False)
            ]

        if self.position_filter != "ALL":
            filtered = filtered[
                filtered["position"].astype(str).str.upper() == self.position_filter
            ]

        self.available_df = filtered.reset_index(drop=True)
        self.refresh_available_players()

    def refresh_available_players(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        if self.available_df is None:
            return

        for _, row in self.available_df.iterrows():
            self.tree.insert(
                "",
                "end",
                values=(
                    row["rank"],
                    row["player_name"],
                    row["team"],
                    row["position"],
                    row["player_projection"],
                    row["adp"],
                    round(row["vor"], 2),
                ),
            )

    def update_draft_status(self):
        if self.current_pick_index >= len(self.draft_order):
            self.round_label.config(text=f"{self.total_rounds}")
            self.pick_label.config(text=f"{len(self.draft_order)}")
            self.clock_label.config(text="Draft Complete")
            return

        current_team = self.draft_order[self.current_pick_index]
        round_number = (self.current_pick_index // self.num_teams) + 1
        pick_number = self.current_pick_index + 1

        self.round_label.config(text=f"{round_number}")
        self.pick_label.config(text=f"{pick_number}")
        self.clock_label.config(text=f"{current_team}")

        self.selected_team.set(current_team)
        self.update_roster_display()
        self.update_recommendations()

    def on_team_change(self, event=None):
        self.update_roster_display()
        self.update_recommendations()

    def update_roster_display(self):
        current_team = self.selected_team.get()
        if not current_team or current_team not in self.teams:
            return

        roster = self.teams[current_team]

        for slot, value in roster.items():
            if value is None:
                self.roster_labels[slot].config(text="--")
            else:
                self.roster_labels[slot].config(text=value)

    def get_team_needs(self, team_name):
        roster = self.teams[team_name]
        needs = []

        if roster["QB"] is None:
            needs.append("QB")
        if roster["RB1"] is None or roster["RB2"] is None:
            needs.append("RB")
        if roster["WR1"] is None or roster["WR2"] is None:
            needs.append("WR")
        if roster["TE"] is None:
            needs.append("TE")
        if roster["FLEX1"] is None or roster["FLEX2"] is None:
            needs.extend(["RB", "WR", "TE"])

        return needs

    def get_recommendations(self, team_name, top_n=3):
        if self.base_df is None or self.base_df.empty:
            return []

        df = self.base_df.copy()
        needs = self.get_team_needs(team_name)

        def score_row(row):
            score = float(row["vor"])

            if row["position"] in needs:
                score += 40

            if row["position"] == "WR":
                score += 8
            elif row["position"] == "TE":
                score += 5
            elif row["position"] == "RB":
                score += 4

            score += float(row["player_projection"]) * 0.01
            return score

        df["recommend_score"] = df.apply(score_row, axis=1)
        df = df.sort_values(by="recommend_score", ascending=False)
        return df.head(top_n).to_dict("records")

    def update_recommendations(self):
        current_team = self.selected_team.get()
        if not current_team or current_team not in self.teams:
            return

        recommendations = self.get_recommendations(current_team, top_n=3)

        for i in range(3):
            if i < len(recommendations):
                row = recommendations[i]
                text = (
                    f"{i+1}. {row['player_name']} ({row['position']} - {row['team']})\n"
                    f"Proj: {row['player_projection']} | ADP: {row['adp']} | VOR: {round(row['vor'], 2)}"
                )
                self.recommendation_labels[i].config(text=text)
            else:
                self.recommendation_labels[i].config(text="--")

    def assign_player_to_team(self, team_name, player_name, position, team):
        roster = self.teams[team_name]
        player_display = f"{player_name} ({position} - {team})"

        if position == "QB":
            if roster["QB"] is None:
                roster["QB"] = player_display
                return True

        elif position == "RB":
            if roster["RB1"] is None:
                roster["RB1"] = player_display
                return True
            if roster["RB2"] is None:
                roster["RB2"] = player_display
                return True
            if roster["FLEX1"] is None:
                roster["FLEX1"] = player_display
                return True
            if roster["FLEX2"] is None:
                roster["FLEX2"] = player_display
                return True

        elif position == "WR":
            if roster["WR1"] is None:
                roster["WR1"] = player_display
                return True
            if roster["WR2"] is None:
                roster["WR2"] = player_display
                return True
            if roster["FLEX1"] is None:
                roster["FLEX1"] = player_display
                return True
            if roster["FLEX2"] is None:
                roster["FLEX2"] = player_display
                return True

        elif position == "TE":
            if roster["TE"] is None:
                roster["TE"] = player_display
                return True
            if roster["FLEX1"] is None:
                roster["FLEX1"] = player_display
                return True
            if roster["FLEX2"] is None:
                roster["FLEX2"] = player_display
                return True

        for bench_slot in ["Bench1", "Bench2", "Bench3", "Bench4", "Bench5"]:
            if roster[bench_slot] is None:
                roster[bench_slot] = player_display
                return True

        return False

    def draft_selected_player(self):
        if self.current_pick_index >= len(self.draft_order):
            messagebox.showinfo("Draft Complete", "The draft is already complete.")
            return

        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a player to draft.")
            return

        item = self.tree.item(selected_item[0])
        selected_values = item["values"]

        player_name = selected_values[1]
        nfl_team = selected_values[2]
        position = selected_values[3]

        current_team = self.draft_order[self.current_pick_index]

        success = self.assign_player_to_team(current_team, player_name, position, nfl_team)
        if not success:
            messagebox.showwarning("Roster Full", f"{current_team} roster is full.")
            return

        round_number = (self.current_pick_index // self.num_teams) + 1
        pick_number = self.current_pick_index + 1

        board_text = f"R{round_number} P{pick_number} - {current_team}: {player_name} ({position})"
        recent_text = f"R{round_number} P{pick_number} - {current_team}: {player_name}"

        self.base_df = self.base_df[self.base_df["player_name"] != player_name].reset_index(drop=True)

        if self.recent_picks_listbox is not None:
            self.recent_picks_listbox.insert(0, recent_text)

        if self.draft_board_listbox is not None:
            self.draft_board_listbox.insert(tk.END, board_text)

        self.current_pick_index += 1
        self.apply_filters_and_refresh()
        self.update_draft_status()
        self.update_recommendations()

        messagebox.showinfo("Drafted", f"{current_team} drafted {player_name}.")

    def go_to_next_team(self):
        if self.current_pick_index < len(self.draft_order) - 1:
            self.current_pick_index += 1
            self.update_draft_status()

    def go_to_previous_team(self):
        if self.current_pick_index > 0:
            self.current_pick_index -= 1
            self.update_draft_status()

    def sort_treeview(self, col):
        if self.available_df is None or self.available_df.empty:
            return

        reverse = self.sort_reverse[col]
        numeric_columns = {"rank", "player_projection", "adp", "vor"}

        if col == "rank":
            temp_rank = self.available_df["rank"].astype(str).str.replace("T", "", regex=False)
            self.available_df = self.available_df.assign(_sort_rank=temp_rank.astype(float))
            self.available_df = self.available_df.sort_values(by="_sort_rank", ascending=not reverse)
            self.available_df = self.available_df.drop(columns=["_sort_rank"])

        elif col in numeric_columns:
            self.available_df[col] = self.available_df[col].astype(float)
            self.available_df = self.available_df.sort_values(by=col, ascending=not reverse)

        else:
            self.available_df = self.available_df.sort_values(
                by=col,
                ascending=not reverse,
                key=lambda s: s.astype(str).str.lower()
            )

        self.available_df = self.available_df.reset_index(drop=True)
        self.sort_reverse[col] = not reverse
        self.refresh_available_players()