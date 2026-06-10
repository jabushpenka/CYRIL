from classes.database import CyrilDB

# запуск должен осуществляться в терминале командой:
# uvicorn api:app

def main():
    db = CyrilDB()
    q = db.group_check_hashkey('13', 'privet')
    print(q)
    return

if __name__ == '__main__':
    main()