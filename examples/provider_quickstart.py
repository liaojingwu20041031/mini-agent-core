"""Print available provider presets."""

from mini_agent.adapters.providers import list_provider_presets


def main() -> None:
    for preset in list_provider_presets():
        aliases = ", ".join(preset.aliases) or "-"
        print(f"{preset.name:12} model={preset.default_model:28} base_url={preset.base_url}")
        print(f"{'':12} key_env={preset.api_key_env:28} aliases={aliases}")


if __name__ == "__main__":
    main()
