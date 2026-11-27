
from apscheduler.schedulers.blocking import BlockingScheduler
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

TREND_SCRIPT = BASE_DIR / "trend_detector.py"
COMBINED_SCRIPT = BASE_DIR / "combined_trend_detector.py"


def run_trend_detection():

    print("\nStarting automatic fashion trend detection...")

    try:
        # STEP 1: Run Fashionpedia trend detection
        print("\nRunning Fashionpedia trend detection...")

        subprocess.run(
            [sys.executable, str(TREND_SCRIPT)],
            check=True
        )

        # STEP 2: Run combined trend detection
        print("\nRunning combined trend detection...")

        subprocess.run(
            [sys.executable, str(COMBINED_SCRIPT)],
            check=True
        )

        print("\nAll trend detection tasks completed successfully!")

    except subprocess.CalledProcessError as error:
        print("\nTrend detection failed:", error)


scheduler = BlockingScheduler()

scheduler.add_job(
    run_trend_detection,
    trigger="interval",
    days=3
)

print("Fashion Trend Scheduler started!")
print("Both trend detection scripts will run every 3 days.")

scheduler.start()

