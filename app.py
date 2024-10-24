from flask import Flask, render_template, request, session, redirect, url_for
import hashlib
import subprocess
import time
import logging

app = Flask(__name__)
app.secret_key = "secret_key"  # 设置一个秘密密钥用于 session 加密

# 假设有一个用户数据库，这里使用字典模拟
users_db = {
    'admin': hashlib.sha256(b'lab123').hexdigest(),  # 密码为 'password' 的哈希值
}

wg_config_file = "/root/wg0.conf"
wg_config_template = "/root/wg0-temp.conf"
binary_path = '/usr/bin/wg-quick'
def update_listen_port(port):
    logging.info("using new port:{0}".format(port))
    with open(wg_config_template, 'r+') as file:
        # Read the file contents
        file_contents = file.read()
        # Replace the word "text" with "data"
        new_contents = file_contents.replace('{0}', port)
        # Go back to the beginning of the file
        file.seek(0)
        # Write the new contents to the file
        with open(wg_config_file, 'w+') as wg_file:
            wg_file.write(new_contents)
            wg_file.truncate()

def refresh_wg_interface():
    result = subprocess.run(["rm", '-rf', '/etc/wireguard/wg0.conf'], capture_output=True)
    result = subprocess.run(["cp", wg_config_file, '/etc/wireguard/wg0.conf'], capture_output=True)

    result = subprocess.run([binary_path, 'down', 'wg0'], capture_output=True)
    logging.info("run wg command result: {0}".format(result.stdout.decode()))
    time.sleep(1)
    result = subprocess.run([binary_path, 'up', 'wg0'], capture_output=True)
    logging.info("run wg command result: {0}".format(result.stdout.decode()))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('loggedin'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        if username in users_db and users_db[username] == hashed_password:
            session['username'] = username
            return redirect(url_for('loggedin'))
        else:
            error = "Invalid username or password"
            return render_template('login.html', error=error)

    return render_template('login.html')

@app.route('/loggedin', methods=['GET', 'POST'])
def loggedin():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        user_input = request.form['user_input']
        update_listen_port(user_input)
        refresh_wg_interface()
        return f"You entered: {user_input}"

    return render_template('loggedin.html', username=session['username'])

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='45.32.7.115', port=12345)
