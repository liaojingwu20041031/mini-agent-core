from pathlib import Path

import yaml


def test_models_example_main_models_are_empty():
    data = yaml.safe_load(Path("config/models.yaml.example").read_text(encoding="utf-8"))

    for profile, section in data["profiles"].items():
        main = section.get("roles", {}).get("main")
        if main:
            assert main.get("model", "") == "", profile


def test_committed_models_main_models_are_empty():
    data = yaml.safe_load(Path("config/models.yaml").read_text(encoding="utf-8"))

    for profile, section in data["profiles"].items():
        main = section.get("roles", {}).get("main")
        if main:
            assert main.get("model", "") == "", profile

