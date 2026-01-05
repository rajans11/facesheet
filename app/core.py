import os
from flask import Flask

template_folder_path = os.path.join(os.getcwd(), 'templates')
app = Flask(__name__, template_folder=template_folder_path)