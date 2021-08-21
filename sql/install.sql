DROP DATABASE IF EXISTS trade;
DROP ROLE IF EXISTS bot_console_user;
CREATE USER bot_console_user WITH PASSWORD 'bot_console_user';
CREATE DATABASE trade ENCODING 'UTF8';
GRANT ALL PRIVILEGES ON DATABASE trade TO bot_console_user;