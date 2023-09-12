import os
from dotenv import dotenv_values
from db_access.DbType import DbType

config = {**dotenv_values("../.env")}


def get_var_value(config, varname):
    if not config:
        return os.environ.get(varname)
    else:
        return config[varname]


class VarEnvSecurApi():
    def __init__(self, config=config):
        self.secret_key = get_var_value(config, 'SECRET_KEY')
        self.algorithm = get_var_value(config, 'ALGORITHM')
        self.access_token_expire_minutes = get_var_value(config, 'ACCESS_TOKEN_EXPIRE_MINUTES')


class VarEnvWeatherApi():
    def __init__(self, config=config):
        self.weather_api_key = get_var_value(config, 'WEATHER_API_KEY')
        self.historic_file_id = get_var_value(config, 'HISTORIC_FILE_ID')


class VarEnvInferenceModel():
    def __init__(self, config=config):
        self.model_inference = get_var_value(config, 'MODEL_INFERENCE')
        self.path_artifact = get_var_value(config, 'PATH_ARTIFACT_INFERENCE')
        self.fcst_history = get_var_value(config, 'FCST_HISTORY')
        self.fcst_horizon = get_var_value(config, 'FCST_HORIZON')


class VarEnvMLflow():
    def __init__(self, config=config):
        self.mlflow_server_port = get_var_value(config, 'MLFLOW_SERVER_PORT')


class DbInfo():
    def __init__(self, config=config):
        self.db_env = get_var_value(config, 'DB_ENV')
        if self.db_env == DbType.snowflake.value:
            self.db_name = get_var_value(config, 'DB_SNOWFLAKE')
            self.db_user = get_var_value(config, 'USER_SNOWFLAKE')
            self.db_pwd = get_var_value(config, 'PWD_SNOWFLAKE')
            self.db_account = get_var_value(config, 'ACCOUNT_SNOWFLAKE')
            self.db_warehouse = get_var_value(config, 'WAREHOUSE_SNOWFLAKE')
            self.db_schema = get_var_value(config, 'SCHEMA_SNOWFLAKE')
        elif self.db_env == DbType.mysql.value:
            self.db_host = get_var_value(config, 'DB_MYSQL_HOST')
            self.db_name = get_var_value(config, 'MYSQL_DATABASE')
            self.db_user = get_var_value(config, 'DB_MYSQL_USER')
            self.db_pwd = get_var_value(config, 'MYSQL_ROOT_PASSWORD')


class UrlData():
    def __init__(self, config=config):
        self.url_historical = get_var_value(config, 'URL_HISTORICAL')
