from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, send_file
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)

UPLOAD_FOLDER = 'uploads'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Mock database of users [NEED TO MAKE A DB]
users = {'user1': {'password': 'password1', 'files': []}, 'user2': {'password': 'password2', 'files': []}}

class User(UserMixin):
    pass

@login_manager.user_loader
def load_user(username):
    if username not in users:
        return None

    user = User()
    user.id = username
    return user

@app.route('/')
def index():
    uploaded_files = os.listdir(UPLOAD_FOLDER)
    return render_template('index.html', files=uploaded_files)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users and users[username]['password'] == password:
            user = User()
            user.id = username
            login_user(user)
            return redirect(url_for('index'))
        else:
            return 'Invalid username or password'

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        file1 = request.files['file1']
        file2 = request.files['file2']

        # Save the files to the upload directory
        file1.save(os.path.join(UPLOAD_FOLDER, file1.filename))
       # carrier_file_path = os.path.join(UPLOAD_FOLDER, 'file_name')

        file2.save(os.path.join(UPLOAD_FOLDER, file2.filename))

        # Store the uploaded files in the user's list of files
        current_user_files = users[current_user.id]['files']
        current_user_files.extend([file1.filename, file2.filename])

        

        return 'Files uploaded successfully.'

    return render_template('upload.html')

@app.route('/perform_steganography', methods=['POST'])
@login_required
def perform_steganography():
    # Retrieve form data
    file_path = os.path.join(UPLOAD_FOLDER, request.form['file1'])  # Path to carrier file
    message_path = os.path.join(UPLOAD_FOLDER, request.form['file2'])  # Path to message file
    #start_bit = int(request.form['start_bit']) # what bit to start from 
    #length = int(request.form['length']) 
    #interval = int(request.form['Lth bit'])
    
    with open(file_path, 'rb') as carrier_file:
        carrier_data = bytearray(carrier_file.read())
    
    with open(message_path, 'rb') as message_file:
        message_data = bytearray(message_file.read())

    interval_bit_replacement(file_path,carrier_data, message_data)
    
    # Write modified carrier data back to a new file
    updated_carrier_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'updated_' + os.path.basename(file_path))
    with open(updated_carrier_file_path, 'wb') as updated_carrier_file:
        updated_carrier_file.write(carrier_data)

    # Provide download link for the updated carrier file
    return render_template('download.html', filename=updated_carrier_file)

def interval_bit_replacement(file_path,carrier_data, message_data):
    start_bit = 0
    interval = 2
    # used to keep track of the current bits being extracted from the message data
    message_bit_index = 0
    for i in range(start_bit, len(carrier_data) * 8, interval):
        # Get the byte index and bit index within the byte
        # we can't interact with our byte arrays
        # without it
        byte_index = i // 8
        bit_index = i % 8

        if message_bit_index < len(message_data) * 8:
            # Extract the bit from the message
            message_bit = (message_data[message_bit_index // 8] >> (message_bit_index % 8))
            # Modify the bit in the carrier data without preserving LSB
            carrier_data[byte_index] &= ~(1 << bit_index)  # Clear the bit
            carrier_data[byte_index] |= (message_bit << bit_index)  # Set the bit

            message_bit_index += 1
        else:
            break

    # Write the modified carrier data back to the file
    with open(file_path, 'wb') as carrier_file:
        carrier_file.write(carrier_data)


@app.route('/download_file/', methods=['GET'])
def download_file():
    updated_carrier_filename = request.args.get('filename')
    return send_from_directory(app.config['UPLOAD_FOLDER'], updated_carrier_filename, as_attachment=True)



if __name__ == '__main__':
    app.run(debug=True)
