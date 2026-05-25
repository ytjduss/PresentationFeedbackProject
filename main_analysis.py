from __future__ import annotations

import sys

from PythonAnalysis.main_analysis import run


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법:")
        print("python main_analysis.py <video_path> [model_name]")
        print()
        print("예시:")
        print("python main_analysis.py PythonAnalysis/input/A00_S01_F_F_03_089_02_WA_MO.mp4 small")
        sys.exit(1)

    video_file = sys.argv[1]
    model_name = sys.argv[2] if len(sys.argv) >= 3 else "small"
    run(video_file, model_name)
