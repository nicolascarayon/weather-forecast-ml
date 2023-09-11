/* DROP and CREATE DATABASE are deactivated on free MySql server use for dev environment */

CREATE TABLE USERS (
    USER_ID VARCHAR(255) PRIMARY KEY,
    PWD_HASH VARCHAR(255),
    FIRSTNAME VARCHAR(255),
    LASTNAME VARCHAR(255),
    USER_EMAIL VARCHAR(255),
    POSITION VARCHAR(255),
    CREATE_DATE DATE,
    LAST_UPD_DATE DATE,
    ACTIVE TINYINT
);

CREATE TABLE PERMISSIONS (
    PERMISSION_ID VARCHAR(255) PRIMARY KEY,     
    DESCRIPTION VARCHAR(255)
);

CREATE TABLE USER_PERMISSION (
    USER_ID VARCHAR(255),
    PERMISSION_ID VARCHAR(255),
    FOREIGN KEY(USER_ID) REFERENCES USERS(USER_ID),
    FOREIGN KEY(PERMISSION_ID) REFERENCES PERMISSIONS(PERMISSION_ID)
);

CREATE TABLE CITIES (    
    CITY VARCHAR(255) PRIMARY KEY    
);

CREATE TABLE WEATHER_DATA (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    OBSERVATION_TIME DATETIME,
    TEMPERATURE INT,
    WEATHER_CODE INT,
    WIND_SPEED INT,
    WIND_DEGREE INT,
    WIND_DIR VARCHAR(255),
    PRESSURE INT,
    PRECIP FLOAT,
    HUMIDITY INT,
    CLOUDCOVER INT,
    FEELSLIKE INT,
    UV_INDEX INT,
    VISIBILITY INT,
    TIME VARCHAR(255),
    CITY VARCHAR(255)    
);

CREATE TABLE FORECAST_DATA (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    DATE DATETIME,
    TEMPERATURE FLOAT,
    WIND_SPEED FLOAT,
    WIND_DEGREE FLOAT,
    PRESSURE FLOAT,
    PRECIP FLOAT,
    HUMIDITY FLOAT,
    CLOUDCOVER FLOAT,
    FEELSLIKE FLOAT,
    UV_INDEX FLOAT,
    CITY VARCHAR(255)    
);

CREATE TABLE MODEL_DATA (
    RUN_NAME VARCHAR(255) PRIMARY KEY,    
    MODEL_NAME VARCHAR(255),
    LEARNING_RATE FLOAT,
    FCST_HORIZON INT,
    FCST_HISTORY INT,
    EPOCHS_NUMBER INT,
    BATCH_SIZE INT,
    PADDING_PATCH VARCHAR(255),
    STRIDE INT,
    PATCH_LEN INT,
    DROPOUT INT,
    ATTN_DROPOUT INT,
    D_FF INT,
    D_MODEL INT,
    N_HEADS INT,
    N_LAYERS INT,
    TEMPERATURE_MSE FLOAT,
    TEMPERATURE_MAE FLOAT,
    WIND_SPEED_MSE FLOAT,
    WIND_SPEED_MAE FLOAT,
    WIND_DEGREE_MSE FLOAT,
    WIND_DEGREE_MAE FLOAT,
    PRESSURE_MSE FLOAT,
    PRESSURE_MAE FLOAT,
    PRECIP_MSE FLOAT,
    PRECIP_MAE FLOAT,
    HUMIDITY_MSE FLOAT,
    HUMIDITY_MAE FLOAT,
    CLOUDCOVER_MSE FLOAT,
    CLOUDCOVER_MAE FLOAT,
    FEELSLIKE_MSE FLOAT,
    FEELSLIKE_MAE FLOAT,
    UV_INDEX_MSE FLOAT,
    UV_INDEX_MAE FLOAT
);

INSERT INTO USERS (USER_ID, PWD_HASH, CREATE_DATE, LAST_UPD_DATE, ACTIVE)
VALUES
('external_client', '$2b$12$4mDimtgnr1BfIPFuU.hGK.sZGCzibTzRlgWEliug6IeGoPuZhXnry', CURDATE(), CURDATE(), 1),
('admax', '$2b$12$4mDimtgnr1BfIPFuU.hGK.sZGCzibTzRlgWEliug6IeGoPuZhXnry', CURDATE(), CURDATE(), 1),
('backend', '$2b$12$4mDimtgnr1BfIPFuU.hGK.sZGCzibTzRlgWEliug6IeGoPuZhXnry', CURDATE(), CURDATE(), 1),
('test', '$2b$12$4mDimtgnr1BfIPFuU.hGK.sZGCzibTzRlgWEliug6IeGoPuZhXnry', CURDATE(), CURDATE(), 1),
('user_test', '$2b$12$4mDimtgnr1BfIPFuU.hGK.sZGCzibTzRlgWEliug6IeGoPuZhXnry', CURDATE(), CURDATE(), 1);

INSERT INTO PERMISSIONS (PERMISSION_ID, DESCRIPTION)
VALUES 
('training', 'launch model training'),
('user_management', 'user management'),
('get_data', 'get data from weather api'),
('forecast', 'get 7 days forecast');

INSERT INTO USER_PERMISSION (USER_ID, PERMISSION_ID)
VALUES
('external_client', 'forecast'),
('admax', 'forecast'),
('admax', 'get_data'),
('admax', 'user_management'),
('admax', 'training'),
('backend', 'training'),
('backend', 'get_data');


INSERT INTO CITIES (CITY)
VALUES
('Margaux'),
('Soussan'),
('Macau, FR'),
('Castelnau-de-Medoc'),
('Lamarque, FR'),
('Ludon-Medoc'),
('Arsac');
