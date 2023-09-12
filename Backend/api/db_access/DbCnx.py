import logging
import pandas as pd
from typing import Optional
from datetime import datetime
from logger import LoggingConfig
from db_access.DbType import DbType
from snowflake.sqlalchemy import URL
from sqlalchemy import create_engine
from business.KeyReturn import KeyReturn
from fastapi.responses import HTMLResponse
from business.User import UserAdd, User
from business.UserPermission import UserPermission
from snowflake.connector import DictCursor
from mysql.connector import connect as connect_mysql
from mysql.connector.cursor_cext import CMySQLCursorDict
from snowflake.connector import connect as connect_sf
from config.variables import DbInfo


db_info = DbInfo()

# Logger Import
LoggingConfig.setup_logging()


class DbCnx():

    @staticmethod
    def get_db_cnx(db_cnx_info: DbInfo):
        db_cnx = None
        if db_cnx_info.db_env == DbType.snowflake.value:
            db_cnx = connect_sf(
                user=db_cnx_info.db_user,
                password=db_cnx_info.db_pwd,
                account=db_cnx_info.db_account,
                warehouse=db_cnx_info.db_warehouse,
                database=db_cnx_info.db_name,
                schema=db_cnx_info.db_schema
            )
        elif db_info.db_env == DbType.mysql.value:
            db_cnx = connect_mysql(
                user=db_cnx_info.db_user,
                password=db_cnx_info.db_pwd,
                host=db_cnx_info.db_host,
                database=db_cnx_info.db_name)

        return db_cnx

    @staticmethod
    def get_cursor(db_env: str, ctx):
        """
        Return the appropriate Dictionnary Cursor depending on database environment
        """
        if db_env == DbType.snowflake.value:
            cs = ctx.cursor(DictCursor)
        elif db_env == DbType.mysql.value:
            cs = ctx.cursor(cursor_class=CMySQLCursorDict)
        return cs


class UserDao():

    @staticmethod
    def get_users():
        """
        Get users from table USERS
        """
        ctx = DbCnx.get_db_cnx(db_info)
        cs = DbCnx.get_cursor(db_info.db_env, ctx)
        try:
            request = "SELECT * FROM USERS"
            cs.execute(request)
            users = cs.fetchall()
        finally:
            cs.close()
            ctx.close()

        return {KeyReturn.success.value: users}

    @staticmethod
    def get_permissions():
        """
        Get permissions from table PERMISSIONS
        """
        ctx = DbCnx.get_db_cnx(db_info)
        cs = DbCnx.get_cursor(db_info.db_env, ctx)
        try:
            request = "SELECT * FROM PERMISSIONS"
            cs.execute(request)
            permissions = cs.fetchall()
        finally:
            cs.close()
            ctx.close()

        return {KeyReturn.success.value: permissions}

    @staticmethod
    def user_exists(user_id: str):
        """
        Return a boolean indicating whether the user exists in table USERS
        """
        user = UserDao.get_user(user_id)
        return user is not None

    @staticmethod
    def get_permission_ids():
        """
        Get all permissions from table PERMISSIONS
        """
        ctx = DbCnx.get_db_cnx(db_info)
        cs = DbCnx.get_cursor(db_info.db_env, ctx)
        try:
            request = "SELECT * FROM PERMISSIONS"
            cs.execute(request)
            permissions_dic = cs.fetchall()
            permission_ids = [permission_dic['PERMISSION_ID'] for permission_dic in permissions_dic]
        finally:
            cs.close()
            ctx.close()

        return permission_ids

    @staticmethod
    def get_user_permissions(user_id: str):
        """
        Get all permissions for user_id from table USER_PERMISSION
        """
        ctx = DbCnx.get_db_cnx(db_info)
        cs = DbCnx.get_cursor(db_info.db_env, ctx)
        try:
            request = """
                SELECT * FROM USER_PERMISSION
                WHERE USER_ID = %s
                """
            cs.execute(request, (user_id,))
            permissions = cs.fetchall()
            permission_ids = [permission['PERMISSION_ID'] for permission in permissions]
        except Exception as e:
            msg = f"Failed to get permissions for user '{user_id}'"
            logging.exception(f"{msg} \n {e}")
            return None
        finally:
            cs.close()
            ctx.close()

        return {KeyReturn.success.value: permission_ids}

    @staticmethod
    def get_permission_users(permission_id: str):
        """
        Get all users who have permission with permission_id
        """
        ctx = DbCnx.get_db_cnx(db_info)
        cs = DbCnx.get_cursor(db_info.db_env, ctx)
        try:
            request = """
                SELECT * FROM USER_PERMISSION
                WHERE PERMISSION_ID = %s
                """
            cs.execute(request, (permission_id,))
            users = cs.fetchall()
            user_ids = [user['USER_ID'] for user in users]
        except Exception as e:
            msg = f"Failed to get users with permission '{permission_id}'"
            logging.exception(f"{msg} \n {e}")
            return None
        finally:
            cs.close()
            ctx.close()

        return {KeyReturn.success.value: user_ids}

    @staticmethod
    def user_has_permission(userPermission: UserPermission):
        """
        Return a boolean indicating whether the user_id has the permission permission_id in table USER_PERMISSION
        """
        ctx = DbCnx.get_db_cnx(db_info)
        cs = ctx.cursor(DictCursor)
        try:
            request = """
                SELECT USER_ID, PERMISSION_ID FROM USER_PERMISSION
                WHERE USER_ID = %s AND PERMISSION_ID = %s
                """
            cs.execute(request, (userPermission.user_id, userPermission.permission_id))
            cnt = cs.fetchall()
            has_permission = len(cnt) > 0
        except Exception as e:
            error_msg = (f"Failed to check existence of permission '{userPermission.permission_id}' "
                         f"for user '{userPermission.user_id}' : {e}")
            logging.exception(error_msg)
            return None
        finally:
            cs.close()
            ctx.close()
        return has_permission

    @staticmethod
    def get_user(user_id: str):
        """
        Get user with user_id from table USERS
        """
        ctx = DbCnx.get_db_cnx(db_info)
        cs = DbCnx.get_cursor(db_info.db_env, ctx)
        try:
            request = """SELECT * FROM USERS WHERE USER_ID = %s"""
            cs.execute(request, (user_id,))
            user_dict = cs.fetchone()
            user_dict = {key.lower(): value for key, value in user_dict.items()}
        except Exception as e:
            logging.exception(f"Failed to get user with user_id '{user_id}' \n {e}")
            return None
        finally:
            cs.close()
            ctx.close()

        user = User(**user_dict)
        user.permissions = UserDao.get_user_permissions(user.user_id)[KeyReturn.success.value]
        return user

    @staticmethod
    def add_user(user: UserAdd):
        """
        Add new user in table USERS
        """
        ctx = DbCnx.get_db_cnx(db_info)
        cs = DbCnx.get_cursor(db_info.db_env, ctx)
        try:
            request = """
            INSERT INTO USERS (USER_ID, PWD_HASH, FIRSTNAME, LASTNAME, USER_EMAIL, POSITION,
            CREATE_DATE, LAST_UPD_DATE, ACTIVE)
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_DATE, CURRENT_DATE, %s)
            """
            cs.execute(request, (user.user_id, user.pwd_hash, user.firstname, user.lastname, user.user_email,
                                 user.position, user.active))
            ctx.commit()
        except Exception as e:
            msg = f"User '{user.user_id}' creation failed"
            logging.exception(f"{msg} \n {e}")
            return {KeyReturn.error.value: f"{msg} : {e}"}
        finally:
            cs.close()
            ctx.close()

        msg = f"User '{user.user_id}' created successfully"
        logging.info(msg)
        return {KeyReturn.success.value: msg}

    @staticmethod
    def add_user_permission(userPermission: UserPermission):
        """
        Give permission_id to user_id by adding record in table USER_PERMISSION
        """
        ctx = DbCnx.get_db_cnx(db_info)
        cs = DbCnx.get_cursor(db_info.db_env, ctx)
        try:
            request = """
            INSERT INTO USER_PERMISSION (USER_ID, PERMISSION_ID)
            VALUES (%s, %s)
            """
            cs.execute(request, (userPermission.user_id, userPermission.permission_id))
            ctx.commit()
        except Exception as e:
            msg = f"Failed to give permission '{userPermission.permission_id}' to user '{userPermission.user_id}'"
            logging.exception(f"{msg} \n {e}")
            return {KeyReturn.error.value: f"{msg}"}
        finally:
            cs.close()
            ctx.close()

        msg = f"Permission '{userPermission.permission_id}' successfully given to user '{userPermission.user_id}'"
        logging.info(msg)
        return {KeyReturn.success.value: msg}

    @staticmethod
    def edit_user(user: User):
        """
        Update user in table USERS with user given in input
        """
        ctx = DbCnx.get_db_cnx(db_info)
        cs = DbCnx.get_cursor(db_info.db_env, ctx)

        request = """
            UPDATE USERS SET
            PWD_HASH = %s,
            FIRSTNAME = %s,
            LASTNAME = %s,
            USER_EMAIL = %s,
            POSITION = %s,
            LAST_UPD_DATE = CURRENT_DATE,
            ACTIVE = %s
            WHERE USER_ID = %s
            """
        try:
            cs.execute(request, (user.pwd_hash, user.firstname, user.lastname, user.user_email, user.position,
                                 user.active, user.user_id))
            ctx.commit()
        except Exception as e:
            msg = f"Failed to edit user '{user.user_id}'"
            logging.exception(f"{msg} \n {e}")
            return {KeyReturn.error.value: msg}
        finally:
            cs.close()
            ctx.close()

        msg = f"User '{user.user_id}' successfully updated"
        logging.info(f"{msg}")
        return {KeyReturn.success.value: msg}

    @staticmethod
    def delete_user(user_id: str):
        """
        Delete user_id's permissions from table USER_PERMISSION
        then delete user_id from table USERS
        """
        # delete user's permissions first because of integrity constraints
        UserDao.delete_user_permissions(user_id)
        ctx = DbCnx.get_db_cnx(db_info)
        cs = DbCnx.get_cursor(db_info.db_env, ctx)
        try:
            request = """DELETE FROM USERS WHERE USER_ID = %s"""
            cs.execute(request, (user_id,))
            ctx.commit()
        except Exception as e:
            msg = f"Failed to delete user '{user_id}'"
            logging.exception(f"{msg} \n {e}")
            return {KeyReturn.error.value: msg}
        finally:
            cs.close()
            ctx.close()

        msg = f"User '{user_id}' successfully deleted"
        logging.info(msg)
        return {KeyReturn.success.value: msg}

    @staticmethod
    def delete_user_permission(userPermission: UserPermission):
        """
        Delete record (user_id, permission_id) from table USER_PERMISSION
        """
        ctx = DbCnx.get_db_cnx(db_info)
        cs = DbCnx.get_cursor(db_info.db_env, ctx)
        try:
            request = """DELETE FROM USER_PERMISSION WHERE USER_ID = %s AND PERMISSION_ID = %s"""
            cs.execute(request, (userPermission.user_id, userPermission.permission_id))
            ctx.commit()
        except Exception as e:
            msg = f"Failed to remove permision '{userPermission.permission_id}' to user '{userPermission.user_id}'"
            logging.exception(f"{msg} \n {e}")
            return {KeyReturn.error.value: msg}
        finally:
            cs.close()
            ctx.close()

        msg = f"Permission '{userPermission.permission_id}' successfully removed for user '{userPermission.user_id}'"
        logging.info(msg)
        return {KeyReturn.success.value: msg}

    @staticmethod
    def delete_user_permissions(user_id: str):
        """
        Delete all permissions associated to user_id in table USER_PERMISSION
        """
        ctx = DbCnx.get_db_cnx(db_info)
        cs = DbCnx.get_cursor(db_info.db_env, ctx)
        try:
            request = f"DELETE FROM USER_PERMISSION WHERE USER_ID = '{user_id}'"
            cs.execute(request)
            ctx.commit()
        except Exception as e:
            msg = f"Failed to delete permissions to user '{user_id}'"
            logging.exception(f"{msg} \n {e}")
            return {KeyReturn.error.value: msg}
        finally:
            cs.close()
            ctx.close()

        return {KeyReturn.success.value: f"Permissions for user {user_id} successfully deleted"}

    @staticmethod
    def get_cities():
        """
        Get all cities from table CITIES
        """
        ctx = DbCnx.get_db_cnx(db_info)
        cs = DbCnx.get_cursor(db_info.db_env, ctx)
        try:
            request = "SELECT CITY FROM CITIES"
            cs.execute(request)
            cities_dic = cs.fetchall()
            cities = [city_dic['CITY'] for city_dic in cities_dic]
        finally:
            cs.close()
            ctx.close()

        return cities

    @staticmethod
    def get_last_date_weather(city: str):
        ctx = DbCnx.get_db_cnx(db_info)
        cs = DbCnx.get_cursor(db_info.db_env, ctx)
        request = """SELECT max(OBSERVATION_TIME) as LAST_DATE
                       FROM WEATHER_DATA
                       WHERE CITY = %s
                    """
        try:
            cs.execute(request, (city,))
            last_date_dic = cs.fetchone()
            last_date = last_date_dic['LAST_DATE']
        finally:
            cs.close()
            ctx.close()

        return last_date

    @staticmethod
    async def get_last_id_weather() -> Optional[int]:
        ctx = DbCnx.get_db_cnx(db_info)
        cs = DbCnx.get_cursor(db_info.db_env, ctx)
        request = """SELECT max(ID) as MAX_ID FROM WEATHER_DATA"""
        try:
            cs.execute(request)
            max_id_dic = cs.fetchone()
            max_id = max_id_dic['MAX_ID']
        finally:
            cs.close()
            ctx.close()

        return max_id


    @staticmethod
    async def empty_weather_data():
        ctx = DbCnx.get_db_cnx(db_info)
        cs = DbCnx.get_cursor(db_info.db_env, ctx)
        request = "DELETE FROM WEATHER_DATA"
        try:
            cs.execute(request)
            ctx.commit()
            logging.info("Delete all records from table WEATHER_DATA")
            return {KeyReturn.success.value: "Weather data successfully deleted"}
        except Exception as e:
            logging.error(f"Data deletion from table WEATHER_DATA failed : {e}")
            return {KeyReturn.error.value: f"Weather data deletion failed : {e}"}
        finally:
            cs.close()
            ctx.close()

    @staticmethod
    async def empty_forecast_data():
        ctx = DbCnx.get_db_cnx(db_info)
        cs = DbCnx.get_cursor(db_info.db_env, ctx)
        request = "DELETE FROM FORECAST_DATA"
        try:
            cs.execute(request)
            ctx.commit()
            logging.info("Delete all records from table FORECAST_DATA")
            return {KeyReturn.success.value: "Weather data successfully deleted"}
        except Exception as e:
            logging.error(f"Data deletion from table FORECAST_DATA failed : {e}")
            return {KeyReturn.error.value: f"Weather data deletion failed : {e}"}
        finally:
            cs.close()
            ctx.close()

    @staticmethod
    def get_last_datetime_weather(city: str):
        ctx = DbCnx.get_db_cnx(db_info)
        cs = DbCnx.get_cursor(db_info.db_env, ctx)

        request = """
        SELECT
            MAX(CASE
                WHEN LENGTH(TIME) = 5 THEN CONCAT(SUBSTRING(OBSERVATION_TIME, 1, 11), TIME)
                WHEN LENGTH(TIME) = 4 THEN CONCAT(SUBSTRING(OBSERVATION_TIME, 1, 11), '0', TIME)
                ELSE NULL
            END) as LAST_DATETIME
        FROM
            WEATHER_DATA
        WHERE CITY = %s
        """
        try:
            ctx.commit()
            cs.execute(request, (city,))
            last_datetime_dic = cs.fetchone()
            last_datetime = last_datetime_dic['LAST_DATETIME']
        finally:
            cs.close()
            ctx.close()

        return last_datetime

    @staticmethod
    def get_weather_data():
        """
        Get weather data from table WHEATHER_DATA
        """
        ctx = DbCnx.get_db_cnx(db_info)
        cs = DbCnx.get_cursor(db_info.db_env, ctx)
        try:
            request = "SELECT * FROM WEATHER_DATA"
            cs.execute(request)
            weather_data = cs.fetchall()
        finally:
            cs.close()
            ctx.close()

        return weather_data

    @staticmethod
    def get_weather_data_df():
        weather_dict = UserDao.get_weather_data()
        df = pd.DataFrame(weather_dict)
        df = df.set_index('ID')
        return df

    @staticmethod
    def get_forecast_data(city: str):
        """
        Get weather data from table FORECAST_DATA
        """
        ctx = DbCnx.get_db_cnx(db_info)
        cs = DbCnx.get_cursor(db_info.db_env, ctx)
        try:
            request = "SELECT * FROM FORECAST_DATA WHERE CITY = %s"
            cs.execute(request, (city,))
            forecast_data = cs.fetchall()
        finally:
            cs.close()
            ctx.close()

        return forecast_data

    @staticmethod
    def get_hist_data(city: str, start_date, end_date):
        """
        Get weather data from table WEATHER_DATA on period defined by start_date and end_date
        """
        ctx = DbCnx.get_db_cnx(db_info)
        cs = DbCnx.get_cursor(db_info.db_env, ctx)
        try:
            request = """
                SELECT CONCAT(DATE(OBSERVATION_TIME), 'T', LPAD(HOUR(TIME), 2, '0'), ':',
                LPAD(MINUTE(TIME), 2, '0'), ':', LPAD(SECOND(TIME), 2, '0')) AS DATE,
                TEMPERATURE, WIND_SPEED, WIND_DEGREE, PRESSURE, PRECIP,
                HUMIDITY, CLOUDCOVER, FEELSLIKE, UV_INDEX
                FROM WEATHER_DATA
                WHERE CITY = %s
                AND OBSERVATION_TIME BETWEEN %s AND %s
                """
            cs.execute(request, (city, start_date, end_date))
            hist_data = cs.fetchall()
        finally:
            cs.close()
            ctx.close()

        return hist_data

    @staticmethod
    def get_forecast_data_df(city: str):
        forecast_dict = UserDao.get_forecast_data(city)
        df = pd.DataFrame(forecast_dict)
        if df.empty:
            return {KeyReturn.error.value: f"No forecast data for city {city}"}
        else:
            df.drop('ID', axis=1, inplace=True)
            return {KeyReturn.success.value: df}

    @staticmethod
    def get_hist_data_df(city: str, start_date: str, end_date: str):
        """
        Return a dataframe containing the historitical data from WEATHER_DATA table on period defined
        by start_date and end_date for city

        Expected format for start_date and end_date : 'YYYY-MM-DD'
        """
        hist_dict = UserDao.get_hist_data(city=city, start_date=start_date, end_date=end_date)
        df = pd.DataFrame(hist_dict)
        if df.empty:
            return {KeyReturn.error.value: f"No historitical data for city {city} on period [{start_date}, {end_date}]"}
        else:
            return {KeyReturn.success.value: df}

    @staticmethod
    def get_db_engine(db_info):
        db_env = db_info.db_env
        mysql_host = mysql_db = mysql_usr = mysql_pwd = None
        db_engine = None
        if db_env == "mysql":
            mysql_host, mysql_db, mysql_usr, mysql_pwd = [db_info.db_host,
                                                          db_info.db_name,
                                                          db_info.db_user,
                                                          db_info.db_pwd]
        else:
            raise Exception("Invalid database environment")

        try:
            db_engine = create_engine(f"mysql+mysqlconnector://{mysql_usr}:{mysql_pwd}@{mysql_host}/{mysql_db}",
                                      echo=False)
            return db_engine
        except Exception as e:
            msg = f"Engine creation failed for DB {db_env} : {e}"
            print(msg)
            logging.exception(msg)
        finally:
            return db_engine

    @staticmethod
    async def send_data_from_df_to_db(df: pd.DataFrame, table_name: str, index: str):
        db_engine = UserDao.get_db_engine(db_info)
        if db_engine:
            try:
                df.drop_duplicates(subset=index, keep='first', inplace=True)
                df.to_sql(table_name, con=db_engine, if_exists='append', index=False)
            except Exception as e:
                msg = f"Data insertion into table {table_name} failed : {e}"
                print(msg)
                logging.exception(msg)
                return False
        else:
            msg = "Failed to get db engine"
            print(msg)
            logging.exception(msg)
            return False

    @staticmethod
    def get_logs():
        try:
            # Find the logs
            # log_path = f"logs/app_{datetime.now().strftime('%Y%m%d')}.log"

            # Download log file from S3 bucket
            # s3_access.s3.Object(s3_var_access.bucket_name, log_path).download_file('/tmp/app.log')

            # Read the downloaded log file
            with open('/tmp/app.log', 'r') as log_file:
                logs = log_file.read()

            # Format logs as HTML response
            formatted_logs = "<pre>" + logs + "</pre>"

            return HTMLResponse(content=formatted_logs)

        except Exception as e:
            return f"Error retrieving logs for today: {str(e)}"
