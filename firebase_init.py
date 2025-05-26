import os
import json
from firebase_admin import credentials, firestore, initialize_app

# Initialize Firebase
def init_firebase():
    if not firestore._apps:
        firebase_config_json = os.environ.get("FIREBASE_KEY_JSON")
        if firebase_config_json:
            cred = credentials.Certificate(json.loads(firebase_config_json))
        else:
            cred = credentials.Certificate("firebase-key.json")
        initialize_app(cred)
    return firestore.client()
