import re, getpass, pymysql

password = getpass.getpass("MySQL root password: ")
sql = open("schema.sql", encoding="utf-8").read()
sql = re.sub(r"--[^\n]*", "", sql)  # remove SQL comments

conn = pymysql.connect(host="localhost", user="root", password=password)
with conn.cursor() as cur:
    for stmt in (s.strip() for s in sql.split(";")):
        if stmt:
            cur.execute(stmt)
conn.commit()
conn.close()
print("Database jobready_ai and all 10 tables created.")