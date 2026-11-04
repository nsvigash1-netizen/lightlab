
import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.colors import ListedColormap


class LightLab:

    def __init__(self, root):

        self.root = root
        self.root.title("LightLab 2.0 - Illumination Simulator")
        self.root.geometry("1200x760")
        self.root.minsize(1000, 650)

        self.lights = {}
        self.next_light_id = 0
        self.optimization_summary = None

        self.build_interface()

        # Initial example light
        self.x_entry.insert(0, "2.5")
        self.y_entry.insert(0, "2.0")
        self.height_entry.insert(0, "2.5")
        self.lumens_entry.insert(0, "6000")

        self.add_light(show_message=False)
        self.calculate()

    # =====================================
    # INTERFACE
    # =====================================

    def build_interface(self):

        main = ttk.Frame(self.root, padding=10)
        main.pack(fill="both", expand=True)

        # Scrollable left control panel
        left_container = ttk.Frame(main, width=370)
        left_container.pack(
            side="left",
            fill="y",
            padx=(0, 12)
        )
        left_container.pack_propagate(False)

        left_canvas = tk.Canvas(
            left_container,
            highlightthickness=0,
            width=350
        )

        scrollbar = ttk.Scrollbar(
            left_container,
            orient="vertical",
            command=left_canvas.yview
        )

        left_canvas.configure(
            yscrollcommand=scrollbar.set
        )

        scrollbar.pack(side="right", fill="y")
        left_canvas.pack(side="left", fill="both", expand=True)

        left = ttk.Frame(left_canvas, padding=5)

        window_id = left_canvas.create_window(
            (0, 0),
            window=left,
            anchor="nw"
        )

        left.bind(
            "<Configure>",
            lambda event: left_canvas.configure(
                scrollregion=left_canvas.bbox("all")
            )
        )

        left_canvas.bind(
            "<Configure>",
            lambda event: left_canvas.itemconfigure(
                window_id,
                width=event.width
            )
        )

        # Mouse wheel scrolling
        def scroll_panel(event):
            left_canvas.yview_scroll(
                int(-event.delta / 120),
                "units"
            )

        left_canvas.bind_all(
            "<MouseWheel>",
            scroll_panel
        )

        # Application title
        ttk.Label(
            left,
            text="LIGHTLAB",
            font=("Arial", 23, "bold")
        ).pack(anchor="w", pady=(5, 2))

        ttk.Label(
            left,
            text="Room Illumination Analysis System",
            foreground="gray"
        ).pack(anchor="w", pady=(0, 15))

        # ---------------------------------
        # ROOM DIMENSIONS
        # ---------------------------------

        room_box = ttk.LabelFrame(
            left,
            text="Room Dimensions (metres)",
            padding=10
        )
        room_box.pack(fill="x", pady=5)

        self.width_entry = self.make_field(
            room_box, "Room width:", "5"
        )

        self.length_entry = self.make_field(
            room_box, "Room length:", "4"
        )

        # ---------------------------------
        # DARK ZONE SETTINGS
        # ---------------------------------

        dark_box = ttk.LabelFrame(
            left,
            text="Dark Zone Analysis",
            padding=10
        )
        dark_box.pack(fill="x", pady=5)

        self.target_entry = self.make_field(
            dark_box,
            "Minimum desired lux:",
            "30"
        )

        # ---------------------------------
        # MANUAL LIGHT INPUT
        # ---------------------------------

        light_box = ttk.LabelFrame(
            left,
            text="Add a Light Source",
            padding=10
        )
        light_box.pack(fill="x", pady=5)

        self.x_entry = self.make_field(
            light_box, "X position (m):"
        )

        self.y_entry = self.make_field(
            light_box, "Y position (m):"
        )

        self.height_entry = self.make_field(
            light_box, "Height (m):"
        )

        self.lumens_entry = self.make_field(
            light_box, "Light output (lumens):"
        )

        ttk.Button(
            light_box,
            text="Add Light",
            command=self.add_light
        ).pack(fill="x", pady=6)

        # ---------------------------------
        # INSTALLED LIGHTS
        # ---------------------------------

        list_box = ttk.LabelFrame(
            left,
            text="Installed Lights",
            padding=8
        )
        list_box.pack(fill="x", pady=5)

        columns = ("x", "y", "height", "lumens")

        self.light_table = ttk.Treeview(
            list_box,
            columns=columns,
            show="headings",
            height=5,
            selectmode="extended"
        )

        headings = {
            "x": "X",
            "y": "Y",
            "height": "Height",
            "lumens": "Lumens"
        }

        for column, heading in headings.items():

            self.light_table.heading(
                column,
                text=heading
            )

            self.light_table.column(
                column,
                width=70,
                anchor="center"
            )

        self.light_table.pack(
            fill="x",
            expand=True
        )

        ttk.Button(
            list_box,
            text="Remove Selected Light",
            command=self.remove_light
        ).pack(fill="x", pady=(8, 0))

        # ---------------------------------
        # AUTOMATIC PLACEMENT SETTINGS
        # ---------------------------------

        optimizer_box = ttk.LabelFrame(
            left,
            text="Automatic Light Placement",
            padding=10
        )
        optimizer_box.pack(fill="x", pady=8)

        ttk.Label(
            optimizer_box,
            text="Genetic Algorithm Optimizer",
            font=("Arial", 10, "bold")
        ).pack(anchor="w", pady=(0, 6))

        self.count_entry = self.make_field(
            optimizer_box,
            "Number of lights:",
            "4"
        )

        self.opt_height_entry = self.make_field(
            optimizer_box,
            "Mounting height (m):",
            "2.5"
        )

        self.opt_lumens_entry = self.make_field(
            optimizer_box,
            "Output per light (lm):",
            "6000"
        )

        ttk.Label(
            optimizer_box,
            text=(
                "The optimizer searches for positions "
                "that reduce dark zones and improve "
                "illumination uniformity."
            ),
            foreground="gray",
            wraplength=300
        ).pack(anchor="w", pady=6)

        ttk.Button(
            optimizer_box,
            text="OPTIMIZE LIGHT PLACEMENT",
            command=self.optimize_lights
        ).pack(fill="x", pady=5)

        # ---------------------------------
        # GENERATE MAP
        # ---------------------------------

        ttk.Button(
            left,
            text="GENERATE ILLUMINATION MAP",
            command=self.calculate
        ).pack(fill="x", pady=12)

        # =================================
        # RIGHT SIDE: VISUALIZATION
        # =================================

        right = ttk.Frame(main)
        right.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.figure = Figure(
            figsize=(7, 5.5),
            dpi=100
        )

        self.canvas = FigureCanvasTkAgg(
            self.figure,
            master=right
        )

        self.canvas.get_tk_widget().pack(
            fill="both",
            expand=True
        )

        # ---------------------------------
        # STATISTICS
        # ---------------------------------

        results = ttk.LabelFrame(
            right,
            text="Illumination Statistics",
            padding=12
        )
        results.pack(fill="x", pady=(8, 0))

        self.stats_label = ttk.Label(
            results,
            text="Waiting for calculation...",
            font=("Arial", 10),
            justify="left",
            wraplength=720
        )

        self.stats_label.pack(anchor="w")

        ttk.Label(
            right,
            text=(
                "Physics model: Isotropic point sources, "
                "horizontal floor, no reflected light."
            ),
            foreground="gray"
        ).pack(anchor="w", pady=6)

    # =====================================
    # INPUT FIELD CREATOR
    # =====================================

    def make_field(self, parent, label, default=""):

        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=3)

        ttk.Label(
            frame,
            text=label,
            width=22
        ).pack(side="left")

        entry = ttk.Entry(frame)
        entry.pack(
            side="right",
            fill="x",
            expand=True
        )

        if default:
            entry.insert(0, default)

        return entry

    # =====================================
    # PHYSICS ENGINE
    # =====================================

    @staticmethod
    def illumination_from_specs(X, Y, light_specs):

        E = np.zeros_like(X, dtype=float)

        for x, y, height, lumens in light_specs:

            dx = X - x
            dy = Y - y

            distance = np.sqrt(
                dx**2 + dy**2 + height**2
            )

            # Isotropic point-source model:
            # E = Phi * h / (4 * pi * r^3)

            contribution = (
                lumens * height /
                (4 * np.pi * distance**3)
            )

            E += contribution

        return E

    @staticmethod
    def get_metrics(E, target):

        minimum = float(np.min(E))
        maximum = float(np.max(E))
        average = float(np.mean(E))

        uniformity = (
            minimum / average * 100
            if average > 0 else 0
        )

        dark_mask = E < target

        dark_fraction = float(
            np.mean(dark_mask)
        )

        dark_percentage = dark_fraction * 100

        return {
            "minimum": minimum,
            "maximum": maximum,
            "average": average,
            "uniformity": uniformity,
            "dark_mask": dark_mask,
            "dark_fraction": dark_fraction,
            "dark_percentage": dark_percentage
        }

    # =====================================
    # ADD LIGHT
    # =====================================

    def add_light(self, show_message=True):

        try:

            width = float(self.width_entry.get())
            length = float(self.length_entry.get())

            x = float(self.x_entry.get())
            y = float(self.y_entry.get())

            height = float(self.height_entry.get())
            lumens = float(self.lumens_entry.get())

            values = np.array([
                width, length, x, y, height, lumens
            ])

            if not np.all(np.isfinite(values)):
                raise ValueError(
                    "Enter valid finite numbers."
                )

            if width <= 0 or length <= 0:
                raise ValueError(
                    "Room dimensions must be positive."
                )

            if not (0 <= x <= width):
                raise ValueError(
                    "X position must be inside the room."
                )

            if not (0 <= y <= length):
                raise ValueError(
                    "Y position must be inside the room."
                )

            if height <= 0 or lumens <= 0:
                raise ValueError(
                    "Height and lumens must be positive."
                )

            light_id = self.next_light_id
            self.next_light_id += 1

            self.lights[light_id] = (
                x, y, height, lumens
            )

            self.light_table.insert(
                "",
                "end",
                iid=str(light_id),
                values=(
                    f"{x:.2f}",
                    f"{y:.2f}",
                    f"{height:.2f}",
                    f"{lumens:.0f}"
                )
            )

            self.optimization_summary = None

            if show_message:
                self.calculate()

        except ValueError as error:

            messagebox.showerror(
                "Invalid Input",
                str(error)
            )

    # =====================================
    # REMOVE LIGHT
    # =====================================

    def remove_light(self):

        selected = self.light_table.selection()

        if not selected:

            messagebox.showinfo(
                "No Selection",
                "Select a light to remove."
            )
            return

        for item in selected:

            self.light_table.delete(item)

            self.lights.pop(
                int(item),
                None
            )

        self.optimization_summary = None

        self.calculate()

    # =====================================
    # GENETIC ALGORITHM
    # AUTOMATIC LIGHT PLACEMENT
    # =====================================

    def optimize_lights(self):

        try:

            width = float(self.width_entry.get())
            length = float(self.length_entry.get())

            target = float(self.target_entry.get())

            count = int(self.count_entry.get())

            height = float(
                self.opt_height_entry.get()
            )

            lumens = float(
                self.opt_lumens_entry.get()
            )

            values = np.array([
                width, length, target, height, lumens
            ])

            if not np.all(np.isfinite(values)):
                raise ValueError(
                    "Enter valid finite numbers."
                )

            if width <= 0 or length <= 0:
                raise ValueError(
                    "Room dimensions must be positive."
                )

            if target <= 0:
                raise ValueError(
                    "Target illumination must be positive."
                )

            if not 1 <= count <= 12:
                raise ValueError(
                    "Number of lights must be between 1 and 12."
                )

            if height <= 0 or lumens <= 0:
                raise ValueError(
                    "Light height and output must be positive."
                )

            # ---------------------------------
            # OPTIMIZATION CONFIGURATION
            # ---------------------------------

            population_size = 36
            generations = 45
            grid_points = 40

            rng = np.random.default_rng()

            # Measurement grid
            x_values = np.linspace(
                0, width, grid_points
            )

            y_values = np.linspace(
                0, length, grid_points
            )

            X, Y = np.meshgrid(
                x_values,
                y_values
            )

            # ---------------------------------
            # FITNESS FUNCTION
            # ---------------------------------

            def evaluate(candidate):

                specs = [
                    (
                        float(position[0]),
                        float(position[1]),
                        height,
                        lumens
                    )
                    for position in candidate
                ]

                E = self.illumination_from_specs(
                    X, Y, specs
                )

                metrics = self.get_metrics(
                    E, target
                )

                # Average normalized illumination
                # deficit below the desired threshold.
                deficit = float(
                    np.mean(
                        np.maximum(target - E, 0)
                    ) / target
                )

                dark_fraction = metrics[
                    "dark_fraction"
                ]

                uniformity = (
                    metrics["uniformity"] / 100
                )

                # Lower score is better.
                score = (
                    0.55 * deficit
                    + 0.25 * dark_fraction
                    + 0.20 * (1 - uniformity)
                )

                return (
                    score,
                    dark_fraction,
                    uniformity
                )

            # ---------------------------------
            # INITIAL POPULATION
            # ---------------------------------

            population = rng.uniform(
                low=[0, 0],
                high=[width, length],
                size=(
                    population_size,
                    count,
                    2
                )
            )

            # Seed the first candidate with
            # an evenly spaced grid arrangement.

            columns = max(
                1,
                int(np.ceil(
                    np.sqrt(count * width / length)
                ))
            )

            rows = int(
                np.ceil(count / columns)
            )

            x_grid = (
                np.arange(columns) + 0.5
            ) * width / columns

            y_grid = (
                np.arange(rows) + 0.5
            ) * length / rows

            grid_candidates = np.array([
                [x, y]
                for y in y_grid
                for x in x_grid
            ])

            indices = np.linspace(
                0,
                len(grid_candidates) - 1,
                count
            ).round().astype(int)

            population[0] = grid_candidates[indices]

            # ---------------------------------
            # RUN GENETIC ALGORITHM
            # ---------------------------------

            self.root.config(cursor="watch")
            self.root.update_idletasks()

            for generation in range(generations):

                scores = np.array([
                    evaluate(candidate)[0]
                    for candidate in population
                ])

                # Rank candidates
                order = np.argsort(scores)

                # Elitism: preserve the two best
                new_population = [
                    population[order[0]].copy(),
                    population[order[1]].copy()
                ]

                # Tournament selection
                def select_parent():

                    competitors = rng.integers(
                        0,
                        population_size,
                        size=3
                    )

                    winner = competitors[
                        np.argmin(scores[competitors])
                    ]

                    return population[winner]

                # Mutation gradually decreases
                # as generations progress.
                mutation_scale = (
                    0.15 * (1 - generation / generations)
                    + 0.02
                )

                mutation_sigma = np.array([
                    width * mutation_scale,
                    length * mutation_scale
                ])

                while len(new_population) < population_size:

                    parent1 = select_parent()
                    parent2 = select_parent()

                    # Uniform crossover
                    mask = rng.random(
                        (count, 2)
                    ) < 0.5

                    child = np.where(
                        mask,
                        parent1,
                        parent2
                    )

                    # Random mutation
                    mutation_mask = (
                        rng.random((count, 2)) < 0.25
                    )

                    mutation = rng.normal(
                        0,
                        mutation_sigma,
                        size=(count, 2)
                    )

                    child = (
                        child
                        + mutation * mutation_mask
                    )

                    # Keep positions inside the room
                    child[:, 0] = np.clip(
                        child[:, 0],
                        0,
                        width
                    )

                    child[:, 1] = np.clip(
                        child[:, 1],
                        0,
                        length
                    )

                    new_population.append(child)

                population = np.array(
                    new_population
                )

            # ---------------------------------
            # SELECT BEST ARRANGEMENT
            # ---------------------------------

            final_scores = np.array([
                evaluate(candidate)[0]
                for candidate in population
            ])

            best_index = np.argmin(final_scores)

            best_positions = (
                population[best_index].copy()
            )

            (
                best_score,
                after_dark,
                after_uniformity
            ) = evaluate(best_positions)

            # ---------------------------------
            # MEASURE CURRENT ARRANGEMENT
            # ---------------------------------

            before_dark = None
            before_uniformity = None

            if self.lights:

                old_E = self.illumination_from_specs(
                    X,
                    Y,
                    list(self.lights.values())
                )

                old_metrics = self.get_metrics(
                    old_E,
                    target
                )

                before_dark = old_metrics[
                    "dark_percentage"
                ]

                before_uniformity = old_metrics[
                    "uniformity"
                ]

            # ---------------------------------
            # REPLACE EXISTING LIGHTS
            # ---------------------------------

            self.lights.clear()

            self.light_table.delete(
                *self.light_table.get_children()
            )

            self.next_light_id = 0

            for position in best_positions:

                x = float(position[0])
                y = float(position[1])

                light_id = self.next_light_id
                self.next_light_id += 1

                self.lights[light_id] = (
                    x,
                    y,
                    height,
                    lumens
                )

                self.light_table.insert(
                    "",
                    "end",
                    iid=str(light_id),
                    values=(
                        f"{x:.2f}",
                        f"{y:.2f}",
                        f"{height:.2f}",
                        f"{lumens:.0f}"
                    )
                )

            # ---------------------------------
            # OPTIMIZATION SUMMARY
            # ---------------------------------

            if before_dark is not None:

                dark_change = (
                    before_dark - after_dark * 100
                )

                uniformity_change = (
                    after_uniformity
                    - before_uniformity
                )

                self.optimization_summary = (
                    f"Dark-zone change: "
                    f"{before_dark:.1f}% -> "
                    f"{after_dark * 100:.1f}% "
                    f"({dark_change:+.1f} percentage points)\n"

                    f"Uniformity change: "
                    f"{before_uniformity:.1f}% -> "
                    f"{after_uniformity:.1f}% "
                    f"({uniformity_change:+.1f} percentage points)\n"

                    f"Optimization score: {best_score:.4f}"
                )

            else:

                self.optimization_summary = (
                    f"Optimization completed.\n"
                    f"Dark-zone percentage: "
                    f"{after_dark * 100:.1f}%\n"
                    f"Uniformity: "
                    f"{after_uniformity:.1f}%\n"
                    f"Optimization score: {best_score:.4f}"
                )

            self.calculate()

            self.root.config(cursor="")

            messagebox.showinfo(
                "Optimization Complete",
                "The best arrangement found has been applied."
            )

        except (ValueError, OverflowError) as error:

            self.root.config(cursor="")

            messagebox.showerror(
                "Optimization Error",
                str(error)
            )

    # =====================================
    # MAIN ILLUMINATION CALCULATION
    # =====================================

    def calculate(self):

        try:

            width = float(self.width_entry.get())
            length = float(self.length_entry.get())
            target = float(self.target_entry.get())

            values = np.array([
                width, length, target
            ])

            if not np.all(np.isfinite(values)):
                raise ValueError(
                    "Enter valid finite room dimensions and threshold."
                )

            if width <= 0 or length <= 0:
                raise ValueError(
                    "Room dimensions must be positive."
                )

            if target <= 0:
                raise ValueError(
                    "Illumination threshold must be positive."
                )

            # Handle the case where no lights remain.
            if not self.lights:

                self.figure.clear()

                ax = self.figure.add_subplot(111)

                ax.set_title(
                    "No Light Sources Installed"
                )

                ax.text(
                    0.5,
                    0.5,
                    "Add a light to generate the heatmap",
                    ha="center",
                    va="center",
                    transform=ax.transAxes
                )

                self.canvas.draw()

                self.stats_label.config(
                    text="No light sources installed."
                )

                return

            # Validate light positions
            for x, y, height, lumens in self.lights.values():

                if not (
                    0 <= x <= width
                    and 0 <= y <= length
                ):
                    raise ValueError(
                        "A light is outside the current room dimensions."
                    )

            # ---------------------------------
            # CREATE FLOOR GRID
            # ---------------------------------

            points = 70

            x_values = np.linspace(
                0, width, points
            )

            y_values = np.linspace(
                0, length, points
            )

            X, Y = np.meshgrid(
                x_values,
                y_values
            )

            # ---------------------------------
            # CALCULATE ILLUMINATION
            # ---------------------------------

            E = self.illumination_from_specs(
                X,
                Y,
                list(self.lights.values())
            )

            # ---------------------------------
            # DARK ZONE ANALYSIS
            # ---------------------------------

            metrics = self.get_metrics(
                E,
                target
            )

            dark_mask = metrics["dark_mask"]

            dark_percentage = metrics[
                "dark_percentage"
            ]

            dark_area = (
                width * length
                * metrics["dark_fraction"]
            )

            # ---------------------------------
            # DRAW HEATMAP
            # ---------------------------------

            self.figure.clear()

            ax = self.figure.add_subplot(111)

            heatmap = ax.pcolormesh(
                X,
                Y,
                E,
                shading="auto",
                cmap="inferno"
            )

            # Cyan overlay for dark zones
            dark_overlay = np.ma.masked_where(
                ~dark_mask,
                np.ones_like(E)
            )

            ax.pcolormesh(
                X,
                Y,
                dark_overlay,
                shading="auto",
                cmap=ListedColormap([
                    "deepskyblue"
                ]),
                vmin=0,
                vmax=1,
                alpha=0.4
            )

            # Light positions
            for x, y, height, lumens in self.lights.values():

                ax.scatter(
                    x,
                    y,
                    marker="*",
                    s=150,
                    color="cyan",
                    edgecolors="black",
                    linewidths=0.7
                )

            if dark_mask.any():

                ax.scatter(
                    [],
                    [],
                    marker="s",
                    color="deepskyblue",
                    alpha=0.6,
                    label=f"Below {target:g} lux"
                )

                ax.legend(
                    loc="upper right"
                )

            ax.set_title(
                "Room Illumination Heatmap",
                fontsize=14,
                fontweight="bold"
            )

            ax.set_xlabel(
                "Room width (m)"
            )

            ax.set_ylabel(
                "Room length (m)"
            )

            ax.set_xlim(0, width)
            ax.set_ylim(0, length)

            ax.set_aspect(
                "equal",
                adjustable="box"
            )

            self.figure.colorbar(
                heatmap,
                ax=ax,
                label="Illuminance (lux)"
            )

            self.figure.tight_layout()

            self.canvas.draw()

            # ---------------------------------
            # DISPLAY STATISTICS
            # ---------------------------------

            result_text = (
                f"Minimum illumination:  "
                f"{metrics['minimum']:.2f} lux\n"

                f"Maximum illumination:  "
                f"{metrics['maximum']:.2f} lux\n"

                f"Average illumination:  "
                f"{metrics['average']:.2f} lux\n"

                f"Uniformity:             "
                f"{metrics['uniformity']:.1f}%\n"

                f"------------------------------------------\n"

                f"Target illumination:    "
                f"{target:.2f} lux\n"

                f"Dark-zone area:         "
                f"{dark_area:.2f} m²\n"

                f"Dark-zone percentage:   "
                f"{dark_percentage:.1f}%"
            )

            if self.optimization_summary:

                result_text += (
                    "\n\nOPTIMIZATION RESULTS\n"
                    + self.optimization_summary
                )

            self.stats_label.config(
                text=result_text
            )

        except ValueError as error:

            messagebox.showerror(
                "Calculation Error",
                str(error)
            )


# =====================================
# START APPLICATION
# =====================================

if __name__ == "__main__":

    root = tk.Tk()

    app = LightLab(root)

    root.mainloop()
