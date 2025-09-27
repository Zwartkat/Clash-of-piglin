import yaml

from enums.config_type import ConfigType


class Config:

    _config = {}

    @staticmethod
    def load(config_file="config.yaml"):
        """
        Allows to load provieded config file.
        Provided config type will be used as key to store the loaded config.

        Args:
            config_file (str, optional): Config file to load, it must be in config folder. Defaults to "config.yaml".
            config_type (ConfigType, optional): Key ID of the loaded config. Defaults to ConfigType.MAIN.
        """
        with open(config_file, "r", encoding="utf-8") as f:
            Config._config = yaml.safe_load(f)

    def get(key: str, default=None):
        """
        Retrieve a config value from loaded config.

        Args:
            key (str): Key of the config value to retrieve
            default (_type_, optional): Default value if not found. Defaults to None.

        Returns:
            _type_: config value or default if not found
        """
        return Config._config.get(key, default)

    def get_assets(key: str, default=None):
        assets = Config._config.get("assets_path", {})
        return assets.get(key, default)

    def get_texture(key, default=None):
        textures = Config._config.get("textures", {})
        return textures.get(key, default)

    def TILE_SIZE() -> int:
        return Config.get("tile_size", default=32)
