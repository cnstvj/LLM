
import firebase_admin
from firebase_admin import credentials, auth, firestore, storage
import os

_firebase_initialized = False

def init_firebase():
    global _firebase_initialized
    if _firebase_initialized:
        return
    svc_path = os.environ.get('FIREBASE_SERVICE_ACCOUNT_PATH')
    if not svc_path or not os.path.exists(svc_path):
        raise RuntimeError('FIREBASE_SERVICE_ACCOUNT_PATH not set or file does not exist.')
    cred = credentials.Certificate(svc_path)
    firebase_admin.initialize_app(cred, {
        'storageBucket': os.environ.get('FIREBASE_STORAGE_BUCKET')
    })
    _firebase_initialized = True

def verify_id_token(id_token):
    try:
        decoded = auth.verify_id_token(id_token)
        return decoded
    except Exception as e:
        raise

def get_firestore_client():
    return firestore.client()

def get_storage_bucket():
    return storage.bucket()
