import yaml

from enums.config_key import ConfigKey


class Config:

    _config = {}
    tile_size = 0

    def __init__(self, config_file: str = "config.yaml"):
        self.load(config_file)

    @staticmethod
    def load(config_file: str):
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
        if len(Config._config) == 0:
            Config.load("config.yaml")
        if Config.tile_size == 0:
            Config.tile_size = Config.get(ConfigKey.TILE_SIZE, default=32)
        return Config.tile_size
