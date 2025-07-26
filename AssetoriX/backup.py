import sqlite3

con = sqlite3.connect("db.sqlite3")
with open("backup.sql", "w") as f:
    for line in con.iterdump():
        f.write('%s\n' % line)
con.close()
print("✅ Database dumped to backup.sql")
