import random
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Глобальная переменная для доступа к enumerate в шаблонах
app.jinja_env.globals.update(enumerate=enumerate)

users = {
    "Max": "admin123",
    "Alex": "password1"
}  # Начальные пользователи
current_user = None
orders = []
archived_orders = []
available_products = ["Milk", "Coffee", "Apple", "Carrot", "Orange"]  # Список доступных продуктов
cancel_reasons = ["Нет в наличии", "Ошибка в заказе", "Продукт не доступен"]  # Шаблонные причины отмены

# Логин
@app.route("/login", methods=["GET", "POST"])
def login():
    global current_user
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in users and users[username] == password:
            current_user = username
            return redirect(url_for("home"))
        else:
            return "Login failed. Please try again."
    return render_template("login.html")


# Список для хранения всех архивных заказов
order_archive = []

@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if request.method == "POST":
        for i, order in enumerate(orders):
            if not order.get('archived', False):  # Проверяем, был ли заказ уже отправлен в архив
                for j, product in enumerate(order['products']):
                    if request.form.get(f'ordered_{i}_{j}'):
                        # Обновляем статус на "Ordered"
                        product['status'] = 'Ordered'
                        product['confirm_reason'] = request.form.get(f'confirm_reason_{i}_{j}')
                    
                    if request.form.get(f'cancelled_{i}_{j}'):
                        # Обновляем статус на "Cancelled"
                        product['status'] = 'Cancelled'
                        product['cancel_reason'] = request.form.get(f'cancel_reason_{i}_{j}')
                
                # Добавляем заказ в архив только один раз
                order_archive.append(order)
                order['archived'] = True  # Помечаем заказ как отправленный в архив
        
        Flask('Orders updated successfully!')
        return redirect(url_for('admin_panel'))

    return render_template('admin.html', orders=orders)


@app.route('/archive')
def order_archive_view():
    return render_template('archive.html', archived_orders=order_archive)


# Логаут
@app.route("/logout")
def logout():
    global current_user
    current_user = None
    return redirect(url_for("login"))

# Главная страница для Alex и Max - отправка заказа и просмотр его предыдущих заказов
@app.route("/", methods=["GET", "POST"])
def home():
    global available_products
    if current_user is None:
        return redirect(url_for("login"))

    if request.method == "POST":
        # Если добавляем новый продукт
        if "new_product" in request.form:
            new_product = request.form.get("new_product")
            if new_product and new_product not in available_products:
                available_products.append(new_product)
            return redirect(url_for("home"))

        # Если создаем новый заказ
        products = []
        for i in range(1, 11):
            product_name = request.form.get(f"product_name_{i}")
            quantity = request.form.get(f"quantity_{i}")
            unit = request.form.get(f"unit_{i}")  # Выбираем единицу измерения
            request_text = request.form.get(f"request_{i}")  # Получаем special request
            if product_name and quantity and unit:
                products.append({
                    "name": product_name,
                    "quantity": f"{quantity} {unit}",
                    "request": request_text,
                    "status": "Pending"
                })

        # Сохраняем заказ с текущим временем и датой
        orders.append({
            "user": current_user,
            "products": products,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "order_number": random.randint(1, 10000000)  # Генерируем уникальный номер заказа
        })
        return redirect(url_for("confirmation"))

    # Все заказы текущего пользователя (Pending + Ordered)
    user_orders = [order for order in archived_orders if order["user"] == current_user] + [order for order in orders if order["user"] == current_user]
    user_orders = sorted(user_orders, key=lambda x: x["timestamp"], reverse=True)  # Сортируем по дате: новые заказы сверху

    return render_template("shoppinglist.html", orders=user_orders, available_products=available_products, current_user=current_user)

@app.route("/confirmation")
def confirmation():
    user = current_user  # Если это строка, например "Alex" или "Max"
    home_route = url_for('home')  # Переадресация на домашнюю страницу после подтверждения
    return render_template("confirmation.html", home_route=home_route)

@app.route("/manage_users", methods=["GET"])
def manage_users():
    return render_template("manage_users.html", users=users)

@app.route("/create_user", methods=["POST"])
def create_user():
    new_username = request.form.get("new_username")  # Проверяем наличие ключа 'new_username'
    new_password = request.form.get("new_password")  # Проверяем наличие ключа 'new_password'
    
    if not new_username or not new_password:
        flash("Please provide both username and password.")
        return redirect(url_for("manage_users"))
    
    # Добавление нового пользователя
    users[new_username] = new_password
    flash(f"User {new_username} created successfully!")
    
    return redirect(url_for("manage_users"))

# Редактирование пользователя
@app.route("/edit_user/<username>", methods=["GET", "POST"])
def edit_user(username):
    if request.method == "POST":
        new_username = request.form.get("new_username")
        new_password = request.form.get("new_password")
        
        # Обновление пользователя
        if username in users:
            users[new_username] = new_password
        
        return redirect(url_for("admin_panel"))

    user_data = {"username": username, "password": users.get(username)}
    return render_template("edit_user.html", user=user_data)

# Удаление пользователя
@app.route("/delete_user/<username>", methods=["POST"])
def delete_user(username):
    # Удаление пользователя
    if username in users:
        del users[username]
    
    return redirect(url_for("admin_panel"))

# Страница архива заказов для Max и Alex
@app.route("/archive")
def archive():
    if current_user is None:
        return redirect(url_for("login"))

    user_archives = archived_orders if current_user == "Max" else [order for order in archived_orders if order["user"] == current_user]
    
    return render_template("archive.html", archived_orders=user_archives, current_user=current_user)

# Добавление нового пользователя
@app.route("/add_user", methods=["POST"])
def add_user():
    new_username = request.form["new_username"]
    new_password = request.form["new_password"]
    
    if new_username in users:
        flash("User already exists!")
    else:
        users[new_username] = new_password
        flash(f"User {new_username} created successfully!")

    return redirect(url_for("admin_panel"))

if __name__ == "__main__":
    app.run(debug=True)
