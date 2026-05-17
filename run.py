import subprocess
import sys
import os
import time

def install_dependencies():
    print("Проверка зависимостей...")
    required = ['flask', 'flask-sqlalchemy', 'sqlalchemy']
    for package in required:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            print(f"Установка {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def init_db():
    from app import app, db
    from models import Administrator, Washer, Box, Client, Service, Discount, Order
    
    if not os.path.exists('carwash.db'):
        print("Инициализация базы данных...")
        with app.app_context():
            db.create_all()
            
            # Seed initial data
            if not Administrator.query.first():
                admin = Administrator(
                    a_fname="Иванов",
                    a_name="Иван",
                    a_mname="Иванович",
                    a_login="admin",
                    a_pass="admin123"
                )
                db.session.add(admin)
            
            if not Box.query.first():
                db.session.add(Box(b_id=1, b_status='Свободен'))
                db.session.add(Box(b_id=2, b_status='Свободен'))
            
            if not Washer.query.first():
                washers = [
                    Washer(w_fname="Петров", w_name="Петр", w_status='Свободен'),
                    Washer(w_fname="Сидоров", w_name="Алексей", w_status='Свободен'),
                    Washer(w_fname="Кузнецов", w_name="Дмитрий", w_status='Свободен'),
                    Washer(w_fname="Смирнов", w_name="Сергей", w_status='Свободен'),
                ]
                db.session.add_all(washers)
            
            if not Service.query.first():
                services = [
                    Service(s_name="Экспресс-мойка", s_price=500, s_dur=15),
                    Service(s_name="Стандартная мойка", s_price=800, s_dur=30),
                    Service(s_name="Комплексная мойка", s_price=1500, s_dur=60),
                    Service(s_name="Химчистка салона", s_price=3000, s_dur=120),
                ]
                db.session.add_all(services)
            
            if not Discount.query.first():
                discounts = [
                    Discount(d_marks=5, d_perc=5),
                    Discount(d_marks=10, d_perc=10),
                    Discount(d_marks=20, d_perc=15),
                ]
                db.session.add_all(discounts)

            db.session.commit()
            print("База данных успешно инициализирована и заполнена.")

if __name__ == "__main__":
    install_dependencies()
    # Give a tiny bit of time for imports to be ready if installed
    time.sleep(1)
    init_db()
    
    print("Запуск сервера CarWash Pro System...")
    from app import app
    app.run(host='0.0.0.0', port=3000)
