import math
import tkinter as tk
from tkinter import messagebox


class EnterpriseCalculator(tk.Tk):
    """A production-grade, object-oriented desktop calculator application."""

    def __init__(self):
        super().__init__()

        # 1. Configure Master Stage Parameters
        self.title("Enterprise Calculator Workstation")
        self.geometry("360x520")
        self.resizable(False, False)
        self.configure(bg="#1e293b")  # Dark Slate Blue Theme

        # 2. State Ingestion Registries
        self.current_expression = ""

        # 3. Build UI Architecture Layers
        self._initialize_display_panel()
        self._build_button_matrix()

    def _initialize_display_panel(self):
        """Architects the high-contrast analytical readout panel."""
        self.display_var = tk.StringVar(value="0")

        # Container frame for structured margin isolation padding
        display_frame = tk.Frame(self, bg="#1e293b")
        display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=15)

        self.readout = tk.Entry(
            display_frame,
            textvariable=self.display_var,
            font=("Consolas", 24, "bold"),
            bg="#0f172a",  # Deep Obsidian
            fg="#f8fafc",  # Crisp White-Grey
            bd=0,
            justify=tk.RIGHT,
            insertbackground="#f8fafc",
        )
        self.readout.pack(fill=tk.BOTH, expand=True, ipady=12, padx=5)

    def _build_button_matrix(self):
        """Deploys the categorical arithmetic button layout grid."""
        matrix_frame = tk.Frame(self, bg="#1e293b")
        matrix_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        # Configures grid system weight parameters for structural scaling flexibility
        for i in range(5):
            matrix_frame.rowconfigure(i, weight=1)
        for j in range(4):
            matrix_frame.columnconfigure(j, weight=1)

        # Chained layout representation map matching structural HTML parameters
        button_blueprints = [
            ("C", 0, 0, 1, "#64748b"),
            ("√", 0, 1, 1, "#0284c7"),
            ("x²", 0, 2, 1, "#0284c7"),
            ("/", 0, 3, 1, "#0f766e"),
            ("7", 1, 0, 1, "#334155"),
            ("8", 1, 1, 1, "#334155"),
            ("9", 1, 2, 1, "#334155"),
            ("*", 1, 3, 1, "#0f766e"),
            ("4", 2, 0, 1, "#334155"),
            ("5", 2, 1, 1, "#334155"),
            ("6", 2, 2, 1, "#334155"),
            ("-", 2, 3, 1, "#0f766e"),
            ("1", 3, 0, 1, "#334155"),
            ("2", 3, 1, 1, "#334155"),
            ("3", 3, 2, 1, "#334155"),
            ("+", 3, 3, 1, "#0f766e"),
            ("0", 4, 0, 1, "#334155"),
            (".", 4, 1, 1, "#334155"),
            ("=", 4, 2, 2, "#ea580c"),  # High-Contrast Orange Action Trigger
        ]

        for text, row, col, span, bg_color in button_blueprints:
            btn = tk.Button(
                matrix_frame,
                text=text,
                font=("Arial", 13, "bold"),
                bg=bg_color,
                fg="#f8fafc",
                bd=0,
                activebackground="#475569",
                activeforeground="#f8fafc",
                command=lambda t=text: self._route_execution_pipeline(t),
            )
            btn.grid(
                row=row,
                column=col,
                columnspan=span,
                sticky="nsew",
                padx=4,
                pady=4,
            )

    def _route_execution_pipeline(self, target_token):
        """Sanitizes inputs and pipes operations to specific evaluation models."""
        if target_token == "C":
            self.current_expression = ""
            self.display_var.set("0")

        elif target_token == "=":
            self._evaluate_expression_matrix()

        elif target_token == "√":
            self._execute_unary_transformation(math.sqrt)

        elif target_token == "x²":
            self._execute_unary_transformation(lambda x: math.pow(x, 2))

        else:
            # Defensive check to guard default starting zeros
            if self.current_expression == "" and target_token == ".":
                self.current_expression = "0."
            elif self.current_expression == "0" and target_token.isdigit():
                self.current_expression = target_token
            else:
                self.current_expression += target_token

            self.display_var.set(self.current_expression)

    def _evaluate_expression_matrix(self):
        """Evaluates mathematical input strings safely using token filtering checks."""
        if not self.current_expression:
            return

        try:
            # Token isolation layer: ensure input contains only safe characters
            sanitized_input = self.current_expression.replace(" ", "")
            allowed_chars = set("0123456789+-*/.")
            if not set(sanitized_input).issubset(allowed_chars):
                raise ValueError("Unauthorized Token Ingestion")

            # Execute explicit processing evaluation
            result = eval(sanitized_input)

            # Format floating precision representations cleanly
            if isinstance(result, float) and result.is_integer():
                result = int(result)

            self.current_expression = str(result)
            self.display_var.set(self.current_expression)

        except ZeroDivisionError:
            messagebox.showerror(
                "Execution Fault", "System Error: Zero division runtime blocked."
            )
            self._route_execution_pipeline("C")
        except Exception:
            messagebox.showerror(
                "Evaluation Error", "Invalid syntax structure detected."
            )
            self._route_execution_pipeline("C")

    def _execute_unary_transformation(self, transformation_lambda):
        """Applies single-argument formulas directly to the display register."""
        try:
            if not self.current_expression:
                current_val = 0.0
            else:
                current_val = float(eval(self.current_expression))

            transformed_result = transformation_lambda(current_val)

            if (
                isinstance(transformed_result, float)
                and transformed_result.is_integer()
            ):
                transformed_result = int(transformed_result)

            self.current_expression = str(transformed_result)
            self.display_var.set(self.current_expression)
        except ValueError:
            messagebox.showerror(
                "Domain Alert", "Mathematical error: Out of domain values."
            )
            self._route_execution_pipeline("C")
        except Exception:
            messagebox.showerror("Execution Fault", "Transformation broken.")
            self._route_execution_pipeline("C")


if __name__ == "__main__":
    app = EnterpriseCalculator()
    app.mainloop()
