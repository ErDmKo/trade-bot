SET ROLE 'bot_console_user';

BEGIN;

CREATE TABLE
    "order" (
        "id" serial NOT NULL PRIMARY KEY,
        "pub_date" date not null default CURRENT_DATE,
        "price" integer NOT NULL,
        "pair" varchar(200) NOT NULL
    );

COMMIT;
