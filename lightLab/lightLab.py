
import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class LightLab:

    def __init__(self, root):
        self.root = root
        self.root.title("LightLab - Room Illumination Simulator")
        self.root.geometry("1150x720")
        self.root.minsize(950, 600)

        # Store each light using a unique ID.
        self.lights = {}
        self.next_light_id = 0

        self.build_interface()

        # Add one example light so the application
        # can be tested immediately.
        self.x_entry.insert(0, "2.5")
        self.y_entry.insert(0, "2.0")
        self.height_entry.insert(0, "2.5")
        self.lumens_entry.insert(0, "6000")

        self.add_light(show_message=False)
        self.calculate()

    def build_interface(self):

        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        # LEFT SIDE: Input controls
        left = ttk.Frame(main, width=350)
        left.pack(side="left", fill="y", padx=(0, 15))
        left.pack_propagate(False)

        ttk.Label(
            left,
            text="LIGHTLAB",
            font=("Arial", 22, "bold")
        ).pack(anchor="w", pady=(0, 3))

        ttk.Label(
            left,
            text="Room illumination analysis tool",
            foreground="gray"
        ).pack(anchor="w", pady=(0, 15))

        # Room dimensions
        room_box = ttk.LabelFrame(
            left, text="Room dimensions (metres)", padding=10
        )
        room_box.pack(fill="x", pady=5)

        self.width_entry = self.make_field(
            room_box, "Room width:", "5"
        )
        self.length_entry = self.make_field(
            room_box, "Room length:", "4"
        )

        # Light input section
        light_box = ttk.LabelFrame(
            left, text="Add a light source", padding=10
        )
        light_box.pack(fill="x", pady=10)

        self.x_entry = self.make_field(
            light_box, "X position (m):"
        )
        self.y_entry = self.make_field(
            light_box, "Y position (m):"
        )
        self.height_entry = self.make_field(
            light_box, "Height above floor (m):"
        )
        self.lumens_entry = self.make_field(
            light_box, "Light output (lumens):"
        )

        ttk.Button(
            light_box,
            text="Add Light",
            command=self.add_light
        ).pack(fill="x", pady=(8, 2))

        # List of installed lights
        list_box = ttk.LabelFrame(
            left, text="Installed lights", padding=8
        )
        list_box.pack(fill="both", expand=True, pady=5)

        columns = ("x", "y", "height", "lumens")

        self.light_table = ttk.Treeview(
            list_box,
            columns=columns,
            show="headings",
            height=8,
            selectmode="extended"
        )

        headings = {
            "x": "X",
            "y": "Y",
            "height": "Height",
            "lumens": "Lumens"
        }

        for column, heading in headings.items():
            self.light_table.heading(column, text=heading)
            self.light_table.column(column, width=70, anchor="center")

        self.light_table.pack(fill="both", expand=True)

        ttk.Button(
            list_box,
            text="Remove Selected Light",
            command=self.remove_light
        ).pack(fill="x", pady=(8, 0))

        ttk.Button(
            left,
            text="GENERATE ILLUMINATION MAP",
            command=self.calculate
        ).pack(fill="x", pady=12)

        # RIGHT SIDE: Heatmap and results
        right = ttk.Frame(main)
        right.pack(side="left", fill="both", expand=True)

        self.figure = Figure(figsize=(7, 5.5), dpi=100)
        self.canvas = FigureCanvasTkAgg(
            self.figure, master=right
        )
        self.canvas.get_tk_widget().pack(
            fill="both", expand=True
        )

        # Results panel
        results = ttk.LabelFrame(
            right, text="Illumination statistics", padding=12
        )
        results.pack(fill="x", pady=(10, 0))

        self.stats_label = ttk.Label(
            results,
            text="Add a light and generate a map.",
            font=("Arial", 11),
            justify="left"
        )
        self.stats_label.pack(anchor="w")

        ttk.Label(
            right,
            text="Model assumes isotropic point sources, "
                 "a horizontal floor and no reflected light.",
            foreground="gray"
        ).pack(anchor="w", pady=8)

    def make_field(self, parent, label, default=""):

        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=3)

        ttk.Label(
            frame, text=label, width=23
        ).pack(side="left")

        entry = ttk.Entry(frame)
        entry.pack(side="right", fill="x", expand=True)

        if default:
            entry.insert(0, default)

        return entry

    def add_light(self, show_message=True):

        try:
            room_width = float(self.width_entry.get())
            room_length = float(self.length_entry.get())

            x = float(self.x_entry.get())
            y = float(self.y_entry.get())
            height = float(self.height_entry.get())
            lumens = float(self.lumens_entry.get())

            if room_width <= 0 or room_length <= 0:
                raise ValueError("Room dimensions must be positive.")

            if not (0 <= x <= room_width):
                raise ValueError("X position must be inside the room.")

            if not (0 <= y <= room_length):
                raise ValueError("Y position must be inside the room.")

            if height <= 0 or lumens <= 0:
                raise ValueError("Height and lumens must be positive.")

            light_id = self.next_light_id
            self.next_light_id += 1

            self.lights[light_id] = (x, y, height, lumens)

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

            if show_message:
                self.calculate()

        except ValueError as error:
            messagebox.showerror("Invalid input", str(error))

    def remove_light(self):

        selected = self.light_table.selection()

        if not selected:
            messagebox.showinfo(
                "No selection", "Select a light to remove."
            )
            return

        for item in selected:
            self.light_table.delete(item)
            self.lights.pop(int(item), None)

        self.calculate()

    def calculate(self):

        try:
            width = float(self.width_entry.get())
            length = float(self.length_entry.get())

            if width <= 0 or length <= 0:
                raise ValueError("Room dimensions must be positive.")

            if not self.lights:
                raise ValueError("Add at least one light source.")

            # Validate that all lights are still inside the room.
            for x, y, height, lumens in self.lights.values():
                if not (0 <= x <= width and 0 <= y <= length):
                    raise ValueError(
                        "A light is outside the current room dimensions."
                    )

            # Create a grid of points across the floor.
            points = 70

            x_values = np.linspace(0, width, points)
            y_values = np.linspace(0, length, points)

            X, Y = np.meshgrid(x_values, y_values)

            # Initially, illumination is zero everywhere.
            E = np.zeros_like(X, dtype=float)

            # Calculate the contribution of every light.
            for x, y, height, lumens in self.lights.values():

                dx = X - x
                dy = Y - y

                distance = np.sqrt(
                    dx**2 + dy**2 + height**2
                )

                # Isotropic point-source illumination model.
                contribution = (
                    lumens * height /
                    (4 * np.pi * distance**3)
                )

                E += contribution

            # Calculate statistics.
            minimum = float(np.min(E))
            maximum = float(np.max(E))
            average = float(np.mean(E))

            uniformity = (
                minimum / average * 100
                if average > 0 else 0
            )

            # Draw the heatmap.
            self.figure.clear()
            ax = self.figure.add_subplot(111)

            heatmap = ax.pcolormesh(
                X, Y, E,
                shading="auto",
                cmap="inferno"
            )

            # Mark the horizontal positions of the lights.
            for x, y, height, lumens in self.lights.values():
                ax.scatter(
                    x, y,
                    marker="*",
                    s=150,
                    color="cyan",
                    edgecolors="black",
                    linewidths=0.7
                )

            ax.set_title("Room Illumination Heatmap")
            ax.set_xlabel("Room width (m)")
            ax.set_ylabel("Room length (m)")
            ax.set_xlim(0, width)
            ax.set_ylim(0, length)
            ax.set_aspect("equal", adjustable="box")

            self.figure.colorbar(
                heatmap,
                ax=ax,
                label="Illuminance (lux)"
            )

            self.figure.tight_layout()
            self.canvas.draw()

            # Display statistics.
            self.stats_label.config(
                text=(
                    f"Minimum illumination:  {minimum:.2f} lux\n"
                    f"Maximum illumination:  {maximum:.2f} lux\n"
                    f"Average illumination:  {average:.2f} lux\n"
                    f"Uniformity:             {uniformity:.1f}%"
                )
            )

        except ValueError as error:
            messagebox.showerror("Calculation error", str(error))


if __name__ == "__main__":

    root = tk.Tk()
    app = LightLab(root)
    root.mainloop()
