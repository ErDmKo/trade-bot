sudo -u postgres psql -c "DROP DATABASE IF EXISTS trade"
sudo -u postgres psql -c "DROP ROLE IF EXISTS bot_console_user"
sudo -u postgres psql -c "CREATE USER bot_console_user WITH PASSWORD 'bot_console_user';"
sudo -u postgres psql -c "CREATE DATABASE trade ENCODING 'UTF8';" 
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE trade TO bot_console_user;"

# cat sql/create_tables.sql | sudo -u postgres psql -d trade -a 
# select round(price::numeric, -2), sum(price::numeric * amount::numeric), count(*) from public.order where (extra::jsonb->>'is_exceed') != '1' and pair='btc_usd' group by round(price::numeric, -2) order by count(*) DESC limit 20
