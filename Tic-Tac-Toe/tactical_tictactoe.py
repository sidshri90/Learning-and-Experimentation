import tkinter as tk
from tkinter import messagebox


class TacticalTicTacToe(tk.Tk):
    """An enterprise-grade Tic-Tac-Toe layout application featuring custom vector themes."""

    def __init__(self):
        super().__init__()

        # 1. Configure Primary Figure Geometry Layers
        self.title("Tactical Matrix Engine")
        self.geometry("400x540")
        self.resizable(False, False)
        self.configure(bg="#0f172a")  # Matte Obsidian Theme

        # 2. Immutable Win Path Matrix Tensors
        self.WIN_COMBINATIONS = [
            [0, 1, 2],
            [3, 4, 5],
            [6, 7, 8],  # Horizontal
            [0, 3, 6],
            [1, 4, 7],
            [2, 5, 8],  # Vertical
            [0, 4, 8],
            [2, 4, 6],  # Diagonal
        ]

        # 3. Core Engine State Registries
        self.active_player = "X"
        self.game_running = True
        self.board_state = ["" for _ in range(9)]
        self.grid_cells = []

        # 4. Construct Component Sub-Panels
        self._initialize_status_banner()
        self._build_matrix_canvas()
        self._deploy_system_controls()

    def _initialize_status_banner(self):
        """Constructs the administrative executive readout header panel."""
        self.status_var = tk.StringVar(value="Active Strategy: Player X Initializing")
        self.banner = tk.Label(
            self,
            textvariable=self.status_var,
            font=("Arial", 12, "bold"),
            bg="#1e293b",
            fg="#38bdf8",  # High-Visibility Cobalt Blue
            pady=12,
        )
        self.banner.pack(fill=tk.X, padx=15, pady=15)

    def _build_matrix_canvas(self):
        """Deploys a responsive grid layout array across the coordinate block."""
        canvas_wrapper = tk.Frame(self, bg="#0f172a")
        canvas_wrapper.pack(padx=20, pady=5)

        for idx in range(9):
            row_idx = idx // 3
            col_idx = idx % 3

            # Instantiate high-contrast structural button cells
            cell = tk.Button(
                canvas_wrapper,
                text="",
                font=("Consolas", 24, "bold"),
                bg="#1e293b",
                fg="#f8fafc",
                bd=1,
                relief="solid",
                highlightthickness=0,
                activebackground="#334155",
                activeforeground="#f8fafc",
                width=5,      # Moved from .grid() to here
                height=2,     # Moved from .grid() to here
                command=lambda i=idx: self._process_player_action(i),
            )
            cell.grid(row=row_idx, column=col_idx, padx=4, pady=4)
            self.grid_cells.append(cell)

    def _deploy_system_controls(self):
        """Injects global system executive control parameters."""
        reset_btn = tk.Button(
            self,
            text="RESET ENGINE MATRIX",
            font=("Arial", 11, "bold"),
            bg="#0f766e",  # Deep Corporate Teal
            fg="#f8fafc",
            bd=0,
            activebackground="#0d9488",
            activeforeground="#f8fafc",
            command=self._reset_system_state,
        )
        reset_btn.pack(fill=tk.X, padx=20, pady=25, ipady=8)

    def _process_player_action(self, target_index):
        """Evaluates cell availability and advances execution pipelines."""
        if not self.game_running or self.board_state[target_index] != "":
            return

        # Commit current register changes
        self.board_state[target_index] = self.active_player
        target_cell = self.grid_cells[target_index]

        # Apply player-specific color branding immediately
        cell_color = "#38bdf8" if self.active_player == "X" else "#f43f5e"
        target_cell.configure(text=self.active_player, fg=cell_color, state="disabled", disabledforeground=cell_color)

        # Check win paths
        if self._evaluate_win_paths():
            self.status_var.set(f"SYSTEM TERMINATED: Player {self.active_player} Triumphs!")
            self.banner.configure(fg="#22c55e", bg="#062f4f")  # Victorious Emerald Green Glow
            self.game_running = False
            messagebox.showinfo("Matrix Execution Complete", f"Victory declared. Player {self.active_player} matches all operational nodes.")
            return

        # Check data matrix exhaustion boundaries (Draw)
        if "" not in self.board_state:
            self.status_var.set("SYSTEM ALERT: Matrix Exhaustion - Draw Condition")
            self.banner.configure(fg="#eab308", bg="#451a03")  # Alert Amber Glow
            self.game_running = False
            messagebox.showwarning("Matrix Exhaustion", "Operational limits reached without parity validation.")
            return

        # Swap player register states
        self.active_player = "O" if self.active_player == "X" else "X"
        self.status_var.set(f"Active Strategy: Player {self.active_player} Processing")

    def _evaluate_win_paths(self) -> bool:
        """Runs validation iterations across the structural win vector tensor."""
        for path in self.WIN_COMBINATIONS:
            if (
                self.board_state[path[0]]
                == self.board_state[path[1]]
                == self.board_state[path[2]]
                != ""
            ):
                # Apply structural rendering highlights across the winning vector array
                for node in path:
                    self.grid_cells[node].configure(bg="#15803d")  # Highlight Matrix Nodes
                return True
        return False

    def _reset_system_state(self):
        """Flushes registries and rebuilds clean working workspace environments."""
        self.active_player = "X"
        self.game_running = True
        self.board_state = ["" for _ in range(9)]

        self.banner.configure(bg="#1e293b", fg="#38bdf8")
        self.status_var.set("Active Strategy: Player X Initializing")

        for cell in self.grid_cells:
            cell.configure(text="", bg="#1e293b", state="normal")


if __name__ == "__main__":
    app = TacticalTicTacToe()
    app.mainloop()
