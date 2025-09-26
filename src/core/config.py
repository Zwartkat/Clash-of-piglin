import yaml


class Config:

    _config = {}

    @staticmethod
    def load(config_file="config.yaml"):
        with open(config_file, "r", encoding="utf-8") as f:
            Config._config = yaml.safe_load(f)

    def get(key, default=None):
        return Config._config.get(key, default)

    def get_assets(key, default=None):
        assets = Config._config.get("assets_path", {})
        return assets.get(key, default)

    def get_texture(key, default=None):
        textures = Config._config.get("textures", {})
        return textures.get(key, default)

    def TILE_SIZE() -> int:
        return Config.get("tile_size", 32)
