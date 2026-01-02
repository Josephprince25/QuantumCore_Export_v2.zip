import firebase_admin
from firebase_admin import credentials, firestore
import os
import logging

logger = logging.getLogger(__name__)

class FirebaseManager:
    def __init__(self):
        self.db = None
        self.initialized = False
        self.init_firebase()

    def init_firebase(self):
        """
        Initialize Firebase Admin SDK.
        Expects 'firebase_credentials.json' in the root directory
        OR GOOGLE_APPLICATION_CREDENTIALS env var.
        """
        try:
            # Check for credentials file
            cred_path = 'firebase_credentials.json'
            
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                if not firebase_admin._apps:
                    firebase_admin.initialize_app(cred)
                self.db = firestore.client()
                self.initialized = True
                logger.info("Firebase Firestore initialized successfully.")
            else:
                logger.warning("firebase_credentials.json not found. Skipping Firebase init.")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")

    def save_scan_log(self, user_id, user_data, scan_data):
        """
        Save scan results to Firestore 'scan_logs' collection.
        """
        if not self.initialized: return
        
        try:
            doc_ref = self.db.collection('scan_logs').document()
            doc_ref.set({
                'user_id': user_id,
                'username': user_data.get('username'),
                'timestamp': firestore.SERVER_TIMESTAMP,
                'exchanges': scan_data.get('exchanges'),
                'profitable_count': scan_data.get('profitable_count'),
                'total_analyzed': scan_data.get('total_analyzed')
            })
            logger.info(f"Saved scan log to Firestore: {doc_ref.id}")
        except Exception as e:
            logger.error(f"Error saving to Firestore: {e}")

    # You can extend this for User Management if you want to replace SQLite entirely
    # But for now, we'll keep it hybrid (SQLite for Auth, Firebase for Logging) 
    # as rewriting the whole Auth system is complex.

firebase_manager = FirebaseManager()
