from discord import SyncWebhook, File

def send_discord_image(message, image_filename):
    SyncWebhook.from_url(os.environ['DISCORD_WEBHOOK']).send(message, file=File(image_filename))



import asyncio
from slixmpp import ClientXMPP
from slixmpp.exceptions import IqError, IqTimeout
from slixmpp.xmlstream import ElementBase, ET
from slixmpp.stanza import Iq
import traceback
import os
import threading

def sending_successful():
    socketio.emit('event', 'sending_successful')

def sending_failed():
    socketio.emit('event', 'sending_failed')

class SendImage(ClientXMPP):
    def __init__(self, jid, password, recipient, file_path):
        super().__init__(jid, password)

        self.recipient = recipient
        self.file_path = file_path

        # Register plugins
        self.register_plugin('xep_0030')  # Service Discovery
        self.register_plugin('xep_0363')  # HTTP File Upload
        self.register_plugin('xep_0071')  # XHTML-IM

        # Event handlers
        self.add_event_handler("session_start", self.session_start)

    async def session_start(self, event):
        self.send_presence()
        await self.get_roster()

        success = None
        try:
            # Upload the file
            url = await self['xep_0363'].upload_file(self.file_path, timeout=10)
            # url= 'https://chatterboxtown.us:5443/upload/4ae2092272047f1e6d30aa6854eac6b566fcbe30/IrvJaHNhqomCjcXMnx39YYoCsZMLPPFdHfnFdvO2/wahoo4.png'
            print(f"Uploaded file to {url}")

            message = self.make_message(mto=self.recipient)
            message['type'] = 'chat'
            message['body'] = url

            # Create the x element with the OOB namespace
            x_element = ET.Element('{jabber:x:oob}x')
            url_element = ET.SubElement(x_element, 'url')
            url_element.text = url

            # Append the custom element to the message
            message.append(x_element)

            print(message.__str__())
            '''
            <message to="+12345678900@cheogram.com" id="1e967beece5e4f86ba3aaeacf0b06b8b" xml:lang="en" type="chat">
                <body>
                    https://chatterboxtown.us:5443/upload/4ae2092272047f1e6d30aa6854eac6b566fcbe30/IrvJaHNhqomCjcXMnx39YYoCsZMLPPFdHfnFdvO2/wahoo4.png
                </body>
                <x xmlns="jabber:x:oob">
                    <url>
                        https://chatterboxtown.us:5443/upload/4ae2092272047f1e6d30aa6854eac6b566fcbe30/IrvJaHNhqomCjcXMnx39YYoCsZMLPPFdHfnFdvO2/wahoo4.png
                    </url>
                </x>
            </message>
            '''
            message.send()
            print("sent")
            success = True
            sending_successful()
        except IqError as e:
            success = False
            print(f"Could not upload file: {e.iq['error']['text']}")
        except IqTimeout:
            success = False
            print("No response from server.")
        except Exception as e:
            success = False
            print(f"Failed to send image: {e}")
            traceback.print_exc()
        finally:
            if not success:
                sending_failed()
            self.disconnect()

def send_image(number, image_path):
    print(f'sending image {image_path} to {number}')
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    xmpp = SendImage(os.environ['XMPP_USER'], os.environ['XMPP_PASS'], f'{number}@cheogram.com', image_path)
    xmpp.connect()
    xmpp.process(forever=False)
    # sometimes:
    # RuntimeError: Event loop is closed
    # asyncio.exceptions.TimeoutError





from flask import Flask, send_from_directory, jsonify, render_template, request
from flask_socketio import SocketIO
from dotenv import load_dotenv
import base64
import phonenumbers
import json
import datetime


DEFAULT_PORT = 8080
SECRETS_FILE = 'data/.env'
load_dotenv(SECRETS_FILE)



def write_config(config):
    with open('data/config.json', 'w') as f:
        json.dump(config, f, indent=2)

try:
    with open('data/config.json', 'r') as f:
        config = json.load(f)
except:
    config = {}
    write_config(config)

if 'correct_guess' not in config:
    config['correct_guess'] = 0
    write_config(config)

os.makedirs('data/teams', exist_ok=True)


app = Flask(__name__, static_url_path='/static', static_folder='static')
socketio = SocketIO(app)
app.config['TEMPLATES_AUTO_RELOAD'] = True

if 'APP_SECRET_KEY' in os.environ:
    app.secret_key = os.environ['APP_SECRET_KEY']
else:
    print(f'warning: APP_SECRET_KEY not provided in {SECRETS_FILE}, falling back to hardcoded value')
    app.secret_key = 'faowiehf A$WTG@)EWSGag9ferug8(iao3r'



@app.route('/favicon.ico')
def favicon_ico():
    return send_from_directory(app.root_path, 'favicon.ico')

@app.route('/favicon.png')
def favicon_png():
    return send_from_directory(app.root_path, 'favicon.png')


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check_admin_password', methods=['POST'])
def check_admin_password():
    data = request.get_json()
    if data.get('password') == 'admin:' + os.environ['ADMIN_PASSWORD']:
        return 'true'
    else:
        return 'false'

# @app.route('/admin', methods=['GET', 'POST'])
# def admin():
#     if request.form.get('password') == 'admin:' + os.environ['ADMIN_PASSWORD']:
#         return render_template('admin.html')
#     else:
#         return 'access denied', 401

def slug_str(s):
    return '-'.join(''.join([c for c in s.lower() if c.isalnum() or c == ' ']).strip().split())

def timestamp():
    return datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

def make_team_dir(team):
    os.makedirs('data/teams/' + team, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_file():
    data = request.get_json()
    image_data = data.get('imageData')
    team = data.get('team')
    print(team)
    team = slug_str(team)
    print(team)
    if not image_data or not team:
        return "error", 400

    image_data = base64.b64decode(image_data)
    make_team_dir(team)
    filename = 'data/teams/' + team + '/' + timestamp() + '.jpg'
    with open(filename, 'wb') as f:
        f.write(image_data)

    return f"/{filename}"


# Custom static data
@app.route('/data/teams/<path:filename>')
def custom_static(filename):
    print(filename)
    if (filename.endswith('.json')):
        return 'forbidden', 400
    return send_from_directory('data/teams/', filename)


#may throw an exception
def standardize_phone_number(number):
    # convert phone number to +12345678900 format
    return phonenumbers.format_number(phonenumbers.parse(number, 'US'), phonenumbers.PhoneNumberFormat.E164)

@app.route('/send', methods=['POST'])
def send_file():
    data = request.get_json()
    print('/send', data)
    image_url = data.get('imageUrl')
    number = data.get('number')
    if not image_url:
        sending_failed()
        print("error no image_url")
        return "error no image_url", 400
    if not number:
        sending_failed()
        print("error no number")
        return "error no number", 400
    if not image_url.startswith('/data/teams/'):
        sending_failed()
        print("error image_url doesn't start with /data/teams/")
        return "error image_url doesn't start with /data/teams/", 400
    
    # try:
    number = standardize_phone_number(number)

    filename = image_url.replace('/data/teams/', 'data/teams/')
    send_image(number, filename)
    #     return "ok"
    # except Exception as e:
    #     traceback.format_exc()
    #     return "error", 400
    return ''

@app.route('/send_discord', methods=['POST'])
def send_discord():
    data = request.get_json()
    print('/send_discord', data)
    image_url = data.get('imageUrl')
    team = data.get('team', '')
    if not image_url or not team:
        return "error", 400

    if not image_url:
        print("error no image_url")
        return "error no image_url", 400
    if not team:
        print("error no team")
        return "error no team", 400
    if not image_url.startswith('/data/teams/'):
        sending_failed()
        print("error image_url doesn't start with /data/teams/")
        return "error image_url doesn't start with /data/teams/", 400
    
    filename = image_url.replace('/data/teams/', 'data/teams/')
    send_discord_image(team, filename)
    return 'ok'


@app.route('/set_correct_guess', methods=['POST'])
def set_correct_guess():
    data = request.get_json()
    correct_guess = data['correct_guess']
    config['correct_guess'] = correct_guess
    write_config(config)
    return str(config['correct_guess'])

@app.route('/get_correct_guess', methods=['GET'])
def get_correct_guess():
    return str(config['correct_guess'])

def write_team_data(team, data):
    with open('data/teams/' + team + '/data.json', 'w') as f:
        json.dump(data, f, indent=2)

def read_team_data(team):
    try:
        with open('data/teams/' + team + '/data.json', 'r') as f:
            data = json.load(f)
    except:
        data = {'guesses': []}
        write_team_data(team, data)
    return data

@app.route('/make_guess', methods=['POST'])
def make_guess():
    data = request.get_json()
    guess = data.get('guess')
    team = data.get('team', '')
    print(team)
    team = slug_str(team)
    print(team)
    if not guess or not team:
        return "error", 400
    make_team_dir(team)
    team_data = read_team_data(team)
    if len(team_data.get('guesses')) >= team_data.get('num_team_members', 1):
        return "error: out of guesses", 400
    team_data['guesses'].append({'guess': guess, 'correct': config['correct_guess']})
    write_team_data(team, team_data)
    print(guess, config['correct_guess'])
    print(abs(guess - config['correct_guess']), config['percent_off_1']/100 * config['correct_guess'])
    print(abs(guess - config['correct_guess']), config['percent_off_2']/100 * config['correct_guess'])
    if guess == config['correct_guess']:
        team_data['got_close'] = True
        write_team_data(team, team_data)
        return 'correct'
    elif abs(guess - config['correct_guess']) < config['percent_off_1']/100 * config['correct_guess']:
        team_data['got_close'] = True
        write_team_data(team, team_data)
        return 'off_1,' + str(config['percent_off_1'])
    elif abs(guess - config['correct_guess']) < config['percent_off_2']/100 * config['correct_guess']:
        team_data['got_close'] = True
        write_team_data(team, team_data)
        return 'off_2,' + str(config['percent_off_2'])
    else:
        return 'wrong'


@app.route('/get_guesses_left', methods=['GET'])
def get_guesses_left():
    data = request.args
    guess = data.get('guess')
    team = data.get('team', '')
    print(team)
    team = slug_str(team)
    print(team)
    if not team:
        return "error", 400
    make_team_dir(team)
    team_data = read_team_data(team)
    print(team_data)
    if 'got_close' in team_data and team_data['got_close'] == True:
        return str(0)
    guesses_left = team_data.get('num_team_members', 1) - len(team_data.get('guesses', []))
    print(guesses_left)
    return str(guesses_left)


@app.route('/set_num_team_members', methods=['POST'])
def set_num_team_members():
    data = request.get_json()
    num_team_members = data['num_team_members']
    team = data['team']
    team = slug_str(team)
    
    team_data = read_team_data(team)
    team_data['num_team_members'] = num_team_members
    write_team_data(team, team_data)

    return 'ok'

@app.route('/get_num_team_members', methods=['POST'])
def get_num_team_members():
    try:
        data = request.get_json()
        team = data['team']
        team = slug_str(team)
        
        team_data = read_team_data(team)
        return str(team_data.get('num_team_members', ''))
    except:
        traceback.format_exc()
        return ''


@socketio.on('connect')
def handle_connect():
    print('[socket.io] a user connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('[socket.io] a user disconnected')

server_initialized = False
@socketio.on('init')
def handle_init(msg):
    channel = msg.get('channel')
    print(f'[socket.io] init {channel}')
    global server_initialized
    if not server_initialized:
        print('client connected for the first time to server, reloading to get latest client')
        server_initialized = True
        socketio.emit('event', 'reload')

@socketio.on('camera')
def handle_camera(msg):
    print(f'[socket.io] camera {msg}')

@socketio.on('guess')
def handle_guess(msg):
    print(f'[socket.io] guess {msg}')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.getenv('PORT', DEFAULT_PORT)), debug=True)


#TODO sticker for team type/number
#TODO sticker for guessing correct
#TODO 
#TODO 
#TODO 
#TODO 
