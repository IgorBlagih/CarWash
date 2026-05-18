import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from models import db, Administrator, Washer, Box, Client, Service, Order
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///carwash.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'carwash-pro-secret'

db.init_app(app)

# --- API v1 ---

@app.route('/api/v1/clients', methods=['GET', 'POST'])
def manage_clients():
    if request.method == 'POST':
        data = request.json
        new_client = Client(
            c_fname=data['fname'],
            c_name=data['name'],
            c_mname=data.get('mname', ''),
            c_phone=data['phone'],
            c_discount=int(data.get('discount', 0))
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
        client.c_discount = int(data.get('discount', client.c_discount))
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

@app.route('/api/v1/services', methods=['GET', 'POST'])
def manage_services():
    if request.method == 'POST':
        data = request.json
        new_service = Service(
            s_name=data['name'],
            s_price=float(data['price']),
            s_dur=int(data['dur'])
        )
        db.session.add(new_service)
        db.session.commit()
        return jsonify({"message": "Service created", "id": new_service.s_id}), 201
    
    services = Service.query.all()
    return jsonify([{ "id": s.s_id, "name": s.s_name, "price": s.s_price, "dur": s.s_dur } for s in services])

@app.route('/api/v1/services/<int:id>', methods=['PUT', 'DELETE'])
def service_detail(id):
    service = Service.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.json
        service.s_name = data.get('name', service.s_name)
        service.s_price = float(data.get('price', service.s_price))
        service.s_dur = int(data.get('dur', service.s_dur))
        db.session.commit()
        return jsonify({"message": "Service updated"})
    
    if request.method == 'DELETE':
        db.session.delete(service)
        db.session.commit()
        return jsonify({"message": "Service deleted"})

@app.route('/api/v1/orders', methods=['POST'])
def create_order():
    data = request.json
    new_order = Order(
        o_cost=float(data['cost']),
        o_admin=data.get('admin_id', 1),
        o_washer=data['washer_id'],
        o_box=data['box_id'],
        o_client=data['client_id']
    )
    # Обновляем статусы
    box = Box.query.get(data['box_id'])
    washer = Washer.query.get(data['washer_id'])
    if box: box.b_status = 'Занят'
    if washer: washer.w_status = 'Занят'
    
    db.session.add(new_order)
    db.session.commit()
    return jsonify({"message": "Order created", "id": new_order.o_id}), 201

@app.route('/api/v1/orders/<int:id>', methods=['PATCH'])
def update_order(id):
    order = Order.query.get_or_404(id)
    data = request.json
    status = data.get('status')
    if status:
        order.o_status = status
        if status in ['Завершен', 'Отменен']:
            if order.box: order.box.b_status = 'Свободен'
            if order.washer: order.washer.w_status = 'Свободен'
        db.session.commit()
    return jsonify({"message": "Order updated"})

@app.route('/api/v1/washer/<int:id>', methods=['GET'])
def washer_info(id):
    washer = Washer.query.get_or_404(id)
    # Находим текущий активный заказ мойщика
    current_order = Order.query.filter_by(o_washer=id, o_status='В процессе').first()
    box_id = current_order.o_box if current_order else None
    return jsonify({
        "id": washer.w_id,
        "fname": washer.w_fname,
        "name": washer.w_name,
        "mname": washer.w_mname,
        "status": washer.w_status,
        "current_box": box_id
    })

# --- UI Routes ---

@app.route('/')
def index():
    boxes = Box.query.all()
    recent_orders = Order.query.order_by(Order.o_datetime.desc()).limit(5).all()
    clients = Client.query.all()
    washers = Washer.query.filter_by(w_status='Свободен').all()
    services = Service.query.all()
    free_boxes = Box.query.filter_by(b_status='Свободен').all()
    
    stats = {
        "clients_count": Client.query.count(),
        "orders_count": Order.query.count(),
        "today_revenue": db.session.query(db.func.sum(Order.o_cost)).filter(Order.o_status == 'Завершен').scalar() or 0
    }
    return render_template('dashboard.html', 
                          boxes=boxes, 
                          recent_orders=recent_orders, 
                          stats=stats,
                          clients=clients,
                          washers=washers,
                          boxes_free=free_boxes,
                          services=services)

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
    app.run(host='0.0.0.0', port=3000)
