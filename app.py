import Algorithmia
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_file
from functools import wraps
import jwt
from os import environ, path
from PIL import Image
from resizeimage import resizeimage
from pymongo import MongoClient
from shutil import copyfile
from tempfile import NamedTemporaryFile
from uuid import uuid4
from werkzeug.security import generate_password_hash, check_password_hash

# init flask app
app = Flask(__name__, static_url_path='')
app.secret_key = str(uuid4())
app.send_file_max_age_default = 0

# connect to db
db_client = MongoClient()
db = db_client.fullstack_demo
users = db.users

# init db
try:
    if not db.users.list_indexes().alive:
        db.users.create_index('id', unique=True)
except:
    raise SystemExit('Unable to connect to database: please run "mongod --fork --dbpath ./mongodb --logpath ./mongodb/mongodb.log')

# create an Algorithmia client and temp dir in Hosted Data
try:
    algorithmia_api_key = environ['ALGORITHMIA_API_KEY']
except KeyError:
    raise SystemExit('Please set the environment variable ALGORITHMIA_API_KEY, obtained from https://algorithmia.com/user#credentials')
client = Algorithmia.client(algorithmia_api_key)
algo_temp_dir = 'data://.my/temp/'
if not client.dir(algo_temp_dir).exists():
    client.dir(algo_temp_dir).create()

# datastructures
class User():

    def __init__(self, email, password, avatar='/default_avatar.png', name='', bio=''):
        self.id = email
        self.passhash = generate_password_hash(password) if password else None
        self.avatar = avatar
        self.name = name
        self.bio = bio

    def to_dict(self):
        return dict(id=self.id, avatar=self.avatar, name=self.name, bio=self.bio)

    @staticmethod
    def from_dict(user_dict):
        user = User(user_dict['id'], None, user_dict['avatar'], user_dict['name'], user_dict['bio'])
        user.passhash = user_dict['passhash']
        return user
    

def user_loader(email, password=None):
    user_dict = users.find_one({'id': email})
    if not user_dict:
        return None
    if password and not check_password_hash(user_dict['passhash'],password):
        return None
    return User.from_dict(user_dict)

# Algorithmia helper functions
def upload_file_algorithmia(local_filename, unique_id):
    remote_file = algo_temp_dir + unique_id
    client.file(remote_file).putFile(local_filename)
    return remote_file

def is_nude(remote_file):
    try:
        algo = client.algo('sfw/NudityDetection2v/0.2.13')
        return algo.pipe(remote_file).result['nude']
    except Exception as x:
        print(f"ERROR: unable to check {remote_file} for nudity: {x}")
        return False


def auto_crop(remote_file, height, width):
    input = {
        'height': height,
        'width': width,
        'image': remote_file
    }
    try:
        algo = client.algo('opencv/SmartThumbnail/2.2.3')
        return algo.pipe(input).result['output']
    except Exception as x:
        print(f'ERROR:unable to auto-crop {remote_file}: {x}')
        return remote_file

# auth helper functions
def generate_jwt(user):
    return jwt.encode({
        'id': user.id,
        'lat': datetime.now(),
        'exp': datetime.now() + timedelta(minutes=30)},
        app.config['SECRET_KEY'])

    