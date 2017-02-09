# trade-bot

Angular2 + aiohttp + sqlalchemy + postgresql

`cd front && npm install && npm run watch` - to build frontend

`./sql/install.sh` - to create user and db
`python -m server sql create_all` - to create tables
`python -m server` - to run http server it will create history row

`python -m server sql drop_all` - to drop tables
`python -m server sql drop <table>` - to drop <table>
`python -m server sql create <table>` - to create <table>
`python -m server play` - to run player
