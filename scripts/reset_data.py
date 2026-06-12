import shutil
import os
import sqlite3

def reset_data():
    print("Resetting operational data...")
    if os.path.exists("chroma_db"):
        print("Removing chroma_db directory...")
        shutil.rmtree("chroma_db")
        
    if os.path.exists("data/app.db"):
        print("Removing sqlite database...")
        os.remove("data/app.db")
        
    print("Data reset complete.")

if __name__ == "__main__":
    reset_data()
