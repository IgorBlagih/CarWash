import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from models import db, Administrator, Washer, Box, Client, Service, Discount, Order
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///carwash.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

db.init_app(app)

# Mock Redis Session Store (Dictionary-based)
class MockRedisSession:
    def __init__(self):
        self._data = {}

    def set(self, key, value):
        self._data[key] = value

    def get(self, key):
        return self._data.get(key)

    def delete(self, key):
        if key in self._data:
            del self._data[key]

session_store = MockRedisSession()

# --- API v1 Endpoints ---

@app.route('/api/v1/clients', methods=['GET', 'POST'])
def manage_clients():
    if request.method == 'POST':
        data = request.json
        new_client = Client(
            c_fname=data['fname'],
            c_name=data['name'],
            c_mname=data.get('mname', ''),
            c_phone=data['phone'],
            c_discount=data.get('discount', 0)
        )
        db.session.add(new_client)
        db.session.commit()
        return jsonify({"message": "Client created", "id": new_client.c_id}), 201
    
    clients = Client.query.all()
    return jsonify([{
        "id": c.c_id,
        "fname": c.c_fname,
        "name": c.c_name,
        "mname": c.c_mname,
        "phone": c.c_phone,
        "discount": c.c_discount
    } for c in clients])

@app.route('/api/v1/clients/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def client_detail(id):
    client = Client.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.json
        client.c_fname = data.get('fname', client.c_fname)
        client.c_name = data.get('name', client.c_name)
        client.c_mname = data.get('mname', client.c_mname)
        client.c_phone = data.get('phone', client.c_phone)
        client.c_discount = data.get('discount', client.c_discount)
        db.session.commit()
        return jsonify({"message": "Client updated"})
    
    if request.method == 'DELETE':
        db.session.delete(client)
        db.session.commit()
        return jsonify({"message": "Client deleted"})
    
    return jsonify({
        "id": client.c_id,
        "fname": client.c_fname,
        "name": client.c_name,
        "mname": client.c_mname,
        "phone": client.c_phone,
        "discount": client.c_discount
    })

@app.route('/api/v1/services', methods=['GET'])
def list_services():
    services = Service.query.all()
    return jsonify([{
        "id": s.s_id,
        "name": s.s_name,
        "price": s.s_price,
        "dur": s.s_dur
    } for s in services])

@app.route('/api/v1/boxes', methods=['GET'])
def list_free_boxes():
    boxes = Box.query.filter_by(b_status='Свободен').all()
    return jsonify([{"id": b.b_id, "status": b.b_status} for b in boxes])

@app.route('/api/v1/washer', methods=['GET', 'POST', 'DELETE'])
def manage_washers():
    if request.method == 'POST':
        data = request.json
        new_washer = Washer(
            w_fname=data['fname'],
            w_name=data['name'],
            w_mname=data.get('mname', ''),
            w_status='Свободен'
        )
        db.session.add(new_washer)
        db.session.commit()
        return jsonify({"message": "Washer added", "id": new_washer.w_id}), 201
    
    if request.method == 'DELETE':
        id = request.args.get('id')
        washer = Washer.query.get_or_404(id)
        db.session.delete(washer)
        db.session.commit()
        return jsonify({"message": "Washer deleted"})

    washers = Washer.query.all()
    return jsonify([{
        "id": w.w_id,
        "fname": w.w_fname,
        "name": w.w_name,
        "mname": w.w_mname,
        "status": w.w_status
    } for w in washers])

@app.route('/api/v1/orders', methods=['GET', 'POST'])
def manage_orders():
    if request.method == 'POST':
        data = request.json
        new_order = Order(
            o_cost=data['cost'],
            o_admin=data['admin_id'],
            o_washer=data['washer_id'],
            o_box=data['box_id'],
            o_client=data['client_id'],
            o_discount=data.get('discount_id'),
            o_status='В процессе'
        )
        # Update box and washer status
        box = Box.query.get(data['box_id'])
        washer = Washer.query.get(data['washer_id'])
        if box: box.b_status = 'Занят'
        if washer: washer.w_status = 'Занят'
        
        db.session.add(new_order)
        db.session.commit()
        return jsonify({"message": "Order created", "id": new_order.o_id}), 201
    
    orders = Order.query.all()
    return jsonify([{
        "id": o.o_id,
        "datetime": o.o_datetime.isoformat(),
        "status": o.o_status,
        "cost": o.o_cost,
        "client": o.client.c_name if o.client else "N/A",
        "washer": o.washer.w_name if o.washer else "N/A",
        "box": o.o_box
    } for o in orders])

@app.route('/api/v1/orders/<int:id>', methods=['PATCH'])
def update_order_status(id):
    order = Order.query.get_or_404(id)
    data = request.json
    new_status = data.get('status')
    if new_status:
        order.o_status = new_status
        if new_status in ['Завершен', 'Отменен']:
            if order.box: order.box.b_status = 'Свободен'
            if order.washer: order.washer.w_status = 'Свободен'
        db.session.commit()
    return jsonify({"message": "Order status updated"})

# --- UI Routes ---

@app.route('/')
def index():
    boxes = Box.query.all()
    orders = Order.query.order_by(Order.o_datetime.desc()).limit(5).all()
    stats = {
        "clients_count": Client.query.count(),
        "orders_count": Order.query.count(),
        "today_revenue": db.session.query(db.func.sum(Order.o_cost)).filter(Order.o_status == 'Завершен').scalar() or 0
    }
    return render_template('dashboard.html', boxes=boxes, recent_orders=orders, stats=stats)

@app.route('/clients')
def clients_page():
    clients = Client.query.all()
    return render_template('clients.html', clients=clients)

@app.route('/orders')
def orders_page():
    orders = Order.query.all()
    clients = Client.query.all()
    washers = Washer.query.filter_by(w_status='Свободен').all()
    boxes = Box.query.filter_by(b_status='Свободен').all()
    services = Service.query.all()
    return render_template('orders.html', orders=orders, clients=clients, washers=washers, boxes=boxes, services=services)

@app.route('/services')
def services_page():
    services = Service.query.all()
    return render_template('services.html', services=services)

@app.route('/staff')
def staff_page():
    washers = Washer.query.all()
    return render_template('staff.html', washers=washers)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
аа