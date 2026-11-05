import numpy as np
import streamlit as st
from matplotlib.figure import Figure
from matplotlib.colors import ListedColormap


# ------------------------------------------------------------
# LightLab 2.0 — Streamlit edition
# Physics model: isotropic point sources above a horizontal floor.
# Reflections, shadows, walls, and fixture-specific light patterns
# are not included in this simplified model.
# ------------------------------------------------------------

st.set_page_config(
    page_title="LightLab 2.0 | Illumination Simulator",
    page_icon="💡",
    layout="wide",
)


# ------------------------- PHYSICS ENGINE --------------------
def illumination_from_specs(X, Y, light_specs):
    """Calculate floor illuminance from (x, y, height, lumens) lights."""
    E = np.zeros_like(X, dtype=float)

    for x, y, height, lumens in light_specs:
        dx = X - x
        dy = Y - y
        distance = np.sqrt(dx**2 + dy**2 + height**2)
        E += lumens * height / (4 * np.pi * distance**3)

    return E


def get_metrics(E, target):
    minimum = float(np.min(E))
    maximum = float(np.max(E))
    average = float(np.mean(E))
    uniformity = minimum / average * 100 if average > 0 else 0.0
    dark_mask = E < target
    dark_fraction = float(np.mean(dark_mask))

    return {
        "minimum": minimum,
        "maximum": maximum,
        "average": average,
        "uniformity": uniformity,
        "dark_mask": dark_mask,
        "dark_fraction": dark_fraction,
        "dark_percentage": dark_fraction * 100,
    }


def run_genetic_algorithm(width, length, target, count, height, lumens, progress_bar):
    """Return the best light arrangement found by the genetic algorithm."""
    population_size = 36
    generations = 45
    grid_points = 40
    rng = np.random.default_rng()

    x_values = np.linspace(0, width, grid_points)
    y_values = np.linspace(0, length, grid_points)
    X, Y = np.meshgrid(x_values, y_values)

    def evaluate(candidate):
        specs = [
            (float(position[0]), float(position[1]), height, lumens)
            for position in candidate
        ]
        E = illumination_from_specs(X, Y, specs)
        metrics = get_metrics(E, target)
        deficit = float(np.mean(np.maximum(target - E, 0)) / target)
        dark_fraction = metrics["dark_fraction"]
        uniformity = metrics["uniformity"] / 100

        # Lower score is better.
        score = (
            0.55 * deficit
            + 0.25 * dark_fraction
            + 0.20 * (1 - uniformity)
        )
        return score, dark_fraction, uniformity

    population = rng.uniform(
        low=[0, 0],
        high=[width, length],
        size=(population_size, count, 2),
    )

    # Seed one candidate with an evenly spaced arrangement.
    columns = max(1, int(np.ceil(np.sqrt(count * width / length))))
    rows = int(np.ceil(count / columns))
    x_grid = (np.arange(columns) + 0.5) * width / columns
    y_grid = (np.arange(rows) + 0.5) * length / rows
    grid_candidates = np.array([[x, y] for y in y_grid for x in x_grid])
    indices = np.linspace(0, len(grid_candidates) - 1, count).round().astype(int)
    population[0] = grid_candidates[indices]

    for generation in range(generations):
        scores = np.array([evaluate(candidate)[0] for candidate in population])
        order = np.argsort(scores)
        new_population = [
            population[order[0]].copy(),
            population[order[1]].copy(),
        ]

        def select_parent():
            competitors = rng.integers(0, population_size, size=3)
            winner = competitors[np.argmin(scores[competitors])]
            return population[winner]

        mutation_scale = 0.15 * (1 - generation / generations) + 0.02
        mutation_sigma = np.array([width * mutation_scale, length * mutation_scale])

        while len(new_population) < population_size:
            parent1 = select_parent()
            parent2 = select_parent()
            mask = rng.random((count, 2)) < 0.5
            child = np.where(mask, parent1, parent2)
            mutation_mask = rng.random((count, 2)) < 0.25
            mutation = rng.normal(0, mutation_sigma, size=(count, 2))
            child = child + mutation * mutation_mask
            child[:, 0] = np.clip(child[:, 0], 0, width)
            child[:, 1] = np.clip(child[:, 1], 0, length)
            new_population.append(child)

        population = np.array(new_population)
        progress_bar.progress(
            (generation + 1) / generations,
            text=f"Optimizing light positions — generation {generation + 1}/{generations}",
        )

    final_scores = np.array([evaluate(candidate)[0] for candidate in population])
    best_positions = population[int(np.argmin(final_scores))].copy()
    best_score, after_dark, after_uniformity = evaluate(best_positions)

    return best_positions, {
        "score": float(best_score),
        "after_dark": float(after_dark * 100),
        "after_uniformity": float(after_uniformity * 100),
    }


# ------------------------- SESSION STATE ---------------------
if "lights" not in st.session_state:
    st.session_state.lights = {
        0: {"x": 2.5, "y": 2.0, "height": 2.5, "lumens": 6000.0}
    }
if "next_light_id" not in st.session_state:
    st.session_state.next_light_id = 1
if "optimization_summary" not in st.session_state:
    st.session_state.optimization_summary = None


# ------------------------- PAGE HEADER -----------------------
st.title("💡 LightLab 2.0")
st.subheader("Room Illumination Analysis System")
st.write(
    "Simulate floor illumination, identify under-lit regions, and search for "
    "improved light arrangements using a Genetic Algorithm."
)


# ------------------------- SIDEBAR CONTROLS ------------------
st.sidebar.header("Simulation Controls")
st.sidebar.subheader("Room Dimensions")
room_width = st.sidebar.number_input(
    "Room width (m)", min_value=0.1, value=5.0, step=0.5, key="room_width"
)
room_length = st.sidebar.number_input(
    "Room length (m)", min_value=0.1, value=4.0, step=0.5, key="room_length"
)

target = st.sidebar.number_input(
    "Minimum desired illumination (lux)",
    min_value=0.1,
    value=30.0,
    step=5.0,
    key="target_lux",
)

st.sidebar.divider()
st.sidebar.subheader("Add a Light Source")
with st.sidebar.form("add_light_form", clear_on_submit=False):
    light_x = st.number_input("X position (m)", min_value=0.0, value=2.5, step=0.25)
    light_y = st.number_input("Y position (m)", min_value=0.0, value=2.0, step=0.25)
    light_height = st.number_input("Mounting height (m)", min_value=0.1, value=2.5, step=0.25)
    light_lumens = st.number_input("Light output (lumens)", min_value=1.0, value=6000.0, step=500.0)
    add_submitted = st.form_submit_button("Add Light", use_container_width=True)

if add_submitted:
    if light_x > room_width or light_y > room_length:
        st.sidebar.error("The light's X and Y positions must be inside the room.")
    else:
        light_id = st.session_state.next_light_id
        st.session_state.lights[light_id] = {
            "x": float(light_x),
            "y": float(light_y),
            "height": float(light_height),
            "lumens": float(light_lumens),
        }
        st.session_state.next_light_id += 1
        st.session_state.optimization_summary = None
        st.rerun()

st.sidebar.divider()
st.sidebar.subheader("Installed Lights")
if st.session_state.lights:
    light_rows = []
    for light_id, light in st.session_state.lights.items():
        light_rows.append(
            {
                "ID": light_id,
                "X (m)": round(light["x"], 2),
                "Y (m)": round(light["y"], 2),
                "Height (m)": round(light["height"], 2),
                "Lumens": round(light["lumens"]),
            }
        )
    st.sidebar.dataframe(light_rows, hide_index=True, use_container_width=True)

    remove_labels = {
        f"Light {light_id} — ({light['x']:.2f}, {light['y']:.2f})": light_id
        for light_id, light in st.session_state.lights.items()
    }
    selected_label = st.sidebar.selectbox("Select a light to remove", list(remove_labels))
    if st.sidebar.button("Remove Selected Light", use_container_width=True):
        selected_id = remove_labels[selected_label]
        del st.session_state.lights[selected_id]
        st.session_state.optimization_summary = None
        st.rerun()
    if st.sidebar.button("Remove All Lights", use_container_width=True):
        st.session_state.lights.clear()
        st.session_state.optimization_summary = None
        st.rerun()
else:
    st.sidebar.info("No light sources installed.")

st.sidebar.divider()
st.sidebar.subheader("Automatic Light Placement")
st.sidebar.caption("Genetic Algorithm Optimizer")
number_of_lights = st.sidebar.number_input(
    "Number of lights", min_value=1, max_value=12, value=4, step=1
)
optimizer_height = st.sidebar.number_input(
    "Mounting height (m)", min_value=0.1, value=2.5, step=0.25
)
optimizer_lumens = st.sidebar.number_input(
    "Output per light (lumens)", min_value=1.0, value=6000.0, step=500.0
)
optimize_clicked = st.sidebar.button(
    "OPTIMIZE LIGHT PLACEMENT", type="primary", use_container_width=True
)


# ------------------------- OPTIMIZATION ACTION ---------------
if optimize_clicked:
    progress = st.progress(0, text="Preparing the optimizer...")
    try:
        old_specs = [
            (light["x"], light["y"], light["height"], light["lumens"])
            for light in st.session_state.lights.values()
        ]
        grid_x = np.linspace(0, room_width, 40)
        grid_y = np.linspace(0, room_length, 40)
        old_X, old_Y = np.meshgrid(grid_x, grid_y)
        old_metrics = None
        if old_specs:
            old_E = illumination_from_specs(old_X, old_Y, old_specs)
            old_metrics = get_metrics(old_E, target)

        best_positions, result = run_genetic_algorithm(
            float(room_width),
            float(room_length),
            float(target),
            int(number_of_lights),
            float(optimizer_height),
            float(optimizer_lumens),
            progress,
        )

        replacement_lights = {}
        for light_id, position in enumerate(best_positions):
            replacement_lights[light_id] = {
                "x": float(position[0]),
                "y": float(position[1]),
                "height": float(optimizer_height),
                "lumens": float(optimizer_lumens),
            }

        if old_metrics is not None:
            result["before_dark"] = old_metrics["dark_percentage"]
            result["before_uniformity"] = old_metrics["uniformity"]
        else:
            result["before_dark"] = None
            result["before_uniformity"] = None

        st.session_state.lights = replacement_lights
        st.session_state.next_light_id = len(replacement_lights)
        st.session_state.optimization_summary = result
        progress.empty()
        st.rerun()
    except (ValueError, FloatingPointError, OverflowError) as error:
        progress.empty()
        st.sidebar.error(f"Optimization error: {error}")


# ------------------------- MAIN VISUALIZATION ----------------
left_col, right_col = st.columns([1.65, 1])

light_specs = [
    (light["x"], light["y"], light["height"], light["lumens"])
    for light in st.session_state.lights.values()
]

lights_outside_room = [
    light_id
    for light_id, light in st.session_state.lights.items()
    if light["x"] > room_width or light["y"] > room_length
]

with left_col:
    st.markdown("### Room Illumination Heatmap")

    if lights_outside_room:
        st.error(
            "At least one installed light is outside the current room dimensions. "
            "Increase the room size or remove that light before calculating."
        )
    elif not light_specs:
        empty_fig = Figure(figsize=(8, 5.5), dpi=110)
        empty_ax = empty_fig.add_subplot(111)
        empty_ax.set_xlim(0, room_width)
        empty_ax.set_ylim(0, room_length)
        empty_ax.set_xlabel("Room width (m)")
        empty_ax.set_ylabel("Room length (m)")
        empty_ax.set_title("No Light Sources Installed")
        empty_ax.text(
            0.5,
            0.5,
            "Add a light source to generate the heatmap",
            ha="center",
            va="center",
            transform=empty_ax.transAxes,
        )
        empty_ax.set_aspect("equal", adjustable="box")
        st.pyplot(empty_fig, use_container_width=True)
    else:
        points = 70
        x_values = np.linspace(0, room_width, points)
        y_values = np.linspace(0, room_length, points)
        X, Y = np.meshgrid(x_values, y_values)
        E = illumination_from_specs(X, Y, light_specs)
        metrics = get_metrics(E, target)
        dark_area = room_width * room_length * metrics["dark_fraction"]

        fig = Figure(figsize=(8, 5.5), dpi=110)
        ax = fig.add_subplot(111)
        heatmap = ax.pcolormesh(X, Y, E, shading="auto", cmap="inferno")

        dark_overlay = np.ma.masked_where(
            ~metrics["dark_mask"], np.ones_like(E)
        )
        ax.pcolormesh(
            X,
            Y,
            dark_overlay,
            shading="auto",
            cmap=ListedColormap(["deepskyblue"]),
            vmin=0,
            vmax=1,
            alpha=0.4,
        )

        for light in st.session_state.lights.values():
            ax.scatter(
                light["x"],
                light["y"],
                marker="*",
                s=150,
                color="cyan",
                edgecolors="black",
                linewidths=0.7,
            )

        if np.any(metrics["dark_mask"]):
            ax.scatter(
                [],
                [],
                marker="s",
                color="deepskyblue",
                alpha=0.6,
                label=f"Below {target:g} lux",
            )
            ax.legend(loc="upper right")

        ax.set_title("Room Illumination Heatmap", fontsize=14, fontweight="bold")
        ax.set_xlabel("Room width (m)")
        ax.set_ylabel("Room length (m)")
        ax.set_xlim(0, room_width)
        ax.set_ylim(0, room_length)
        ax.set_aspect("equal", adjustable="box")
        fig.colorbar(heatmap, ax=ax, label="Illuminance (lux)")
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)

with right_col:
    st.markdown("### Illumination Statistics")
    if lights_outside_room:
        st.info("Statistics are unavailable until all lights are inside the room.")
    elif not light_specs:
        st.info("No light sources installed. Add a light or run automatic placement.")
    else:
        st.metric("Minimum illumination", f"{metrics['minimum']:.2f} lux")
        st.metric("Maximum illumination", f"{metrics['maximum']:.2f} lux")
        st.metric("Average illumination", f"{metrics['average']:.2f} lux")
        st.metric("Uniformity", f"{metrics['uniformity']:.1f}%")
        st.divider()
        st.metric("Target illumination", f"{target:.2f} lux")
        st.metric("Dark-zone area", f"{dark_area:.2f} m²")
        st.metric("Dark-zone percentage", f"{metrics['dark_percentage']:.1f}%")

        summary = st.session_state.optimization_summary
        if summary:
            st.divider()
            st.markdown("**Optimization results**")
            if summary["before_dark"] is not None:
                st.write(
                    f"Dark-zone percentage: {summary['before_dark']:.1f}% → "
                    f"{summary['after_dark']:.1f}%"
                )
                st.write(
                    f"Uniformity: {summary['before_uniformity']:.1f}% → "
                    f"{summary['after_uniformity']:.1f}%"
                )
            else:
                st.write(f"Dark-zone percentage: {summary['after_dark']:.1f}%")
                st.write(f"Uniformity: {summary['after_uniformity']:.1f}%")
            st.write(f"Optimization score: {summary['score']:.4f} (lower is better)")

st.divider()
st.caption(
    "Physics model: isotropic point sources above a horizontal floor. "
    "The simulation does not include reflected light, shadows, furniture, "
    "walls, or real fixture-specific photometric distributions. "
    "The genetic algorithm is a heuristic search and does not guarantee a global optimum."
)
