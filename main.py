import csv
import time
from pathlib import Path

from grbl_controller import GRBLController


SIMULATION_MODE = True

GRBL_PORT = "COM3"
RESULTS_DIR = Path("data")
RESULTS_FILE = RESULTS_DIR / "grid_test_results.csv"


def fake_touch_read(expected_x, expected_y):
    return {
        "x": expected_x + 0.5,
        "y": expected_y - 0.3,
        "timestamp": time.time(),
    }


def fake_force_read():
    return 100.0


def tap_screen(grbl=None):
    if SIMULATION_MODE:
        print("SIM: tap screen")
        time.sleep(0.2)
        return

    # Current MG90 servo through modified GRBL spindle commands.
    grbl.send_command("M3 S1000")  # pen down / servo down
    grbl.dwell(0.2)
    grbl.send_command("M5")        # pen up / servo up
    grbl.dwell(0.2)


def move_to_point(grbl, x, y):
    if SIMULATION_MODE:
        print(f"SIM: move to X={x:.2f}, Y={y:.2f}")
        time.sleep(0.1)
        return

    grbl.move_to(x=x, y=y, feedrate=1000)


def run_grid_test(grbl=None, rows=3, cols=3, spacing_mm=20):
    RESULTS_DIR.mkdir(exist_ok=True)

    with open(RESULTS_FILE, "w", newline="") as file:
        writer = csv.writer(file)

        writer.writerow([
            "timestamp",
            "target_x_mm",
            "target_y_mm",
            "touch_x",
            "touch_y",
            "force_g",
            "error_x",
            "error_y",
        ])

        for row in range(rows):
            for col in range(cols):
                target_x = col * spacing_mm
                target_y = row * spacing_mm

                move_to_point(grbl, target_x, target_y)
                tap_screen(grbl)

                if SIMULATION_MODE:
                    touch = fake_touch_read(target_x, target_y)
                    force_g = fake_force_read()
                else:
                    # Later replace with real touch + force reads.
                    touch = {"x": None, "y": None, "timestamp": time.time()}
                    force_g = None

                error_x = None
                error_y = None

                if touch["x"] is not None and touch["y"] is not None:
                    error_x = touch["x"] - target_x
                    error_y = touch["y"] - target_y

                writer.writerow([
                    time.time(),
                    target_x,
                    target_y,
                    touch["x"],
                    touch["y"],
                    force_g,
                    error_x,
                    error_y,
                ])

                print(
                    f"Target=({target_x:.2f}, {target_y:.2f}) "
                    f"Touch=({touch['x']}, {touch['y']}) "
                    f"Force={force_g}"
                )


def main():
    grbl = None

    try:
        if not SIMULATION_MODE:
            grbl = GRBLController(port=GRBL_PORT)
            grbl.connect()
            grbl.set_units_mm()
            grbl.set_absolute_mode()

        run_grid_test(
            grbl=grbl,
            rows=3,
            cols=3,
            spacing_mm=20,
        )

        print(f"Results saved to: {RESULTS_FILE}")

    finally:
        if grbl is not None:
            grbl.disconnect()


if __name__ == "__main__":
    main()
