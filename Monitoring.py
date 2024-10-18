import os
import hashlib
import time
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Directory to monitor
MONITOR_DIR = '/Users/csuftitan/Desktop/FileMonitor'

# File to store the hash data
HASH_FILE = 'file_hashes.json'

# Time interval for monitoring (in seconds)
MONITOR_INTERVAL = 10

# Email configuration
SENDER_EMAIL = 'your email'  # Replace with your email
SENDER_PASSWORD = 'your password'  # Replace with your email password
RECIPIENT_EMAIL = 'recipient email'  # Replace with recipient's email
SMTP_SERVER = 'smtp.gmail.com'  # Replace with your SMTP server (e.g., 'smtp.gmail.com')
SMTP_PORT = 587  # Common port for SMTP

# Function to calculate the SHA-256 hash of a file
def calculate_hash(file_path):
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error calculating hash for {file_path}: {e}")
        return None


# Function to get the hash dictionary of the current files in the directory
def get_file_hashes(directory):
    file_hashes = {}
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_hash = calculate_hash(file_path)
            if file_hash:
                file_hashes[file_path] = file_hash
            else:
                print(f"Skipping file {file_path} (could not calculate hash)")
    return file_hashes


# Function to load previous file hashes
def load_hashes(hash_file):
    if os.path.exists(hash_file):
        with open(hash_file, 'r') as f:
            return json.load(f)
    return {}


# Function to save current file hashes
def save_hashes(hash_file, file_hashes):
    with open(hash_file, 'w') as f:
        json.dump(file_hashes, f, indent=4)


# Function to send email alerts
def send_email_alert(modified_files):
    subject = "File Integrity Alert: Files Modified"
    body = "Hello, Please note theat the following files have been modified:\n\n" + "\n".join(modified_files)
    
    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to the SMTP server and send the email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Upgrade the connection to a secure encrypted SSL/TLS connection
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
        print(f"Email alert sent to {RECIPIENT_EMAIL} for modified files.")
    except Exception as e:
        print(f"Failed to send email: {e}")


# Function to monitor file integrity
def monitor_files(directory, hash_file, interval):
    print(f"Monitoring directory: {directory} every {interval} seconds...")

    # Load the previous hash data
    previous_hashes = load_hashes(hash_file)
    print(f"Loaded {len(previous_hashes)} previous file hashes.")

    while True:
        # Get the current hashes of files in the directory
        current_hashes = get_file_hashes(directory)
        print(f"Scanned {len(current_hashes)} files in the directory.")

        modified_files = []
        deleted_files = []
        new_files = []

        # Check for file modifications and deletions
        for file_path, file_hash in previous_hashes.items():
            if file_path not in current_hashes:
                deleted_files.append(file_path)  # File was deleted
            elif current_hashes[file_path] != file_hash:
                modified_files.append(file_path)  # File was modified

        # Check for new files
        for file_path in current_hashes:
            if file_path not in previous_hashes:
                new_files.append(file_path)  # New file detected

        # Log changes
        if modified_files or deleted_files or new_files:
            print("\nChanges detected:")
            if modified_files:
                for file in modified_files:
                    print(f"Modified file: {file}")
                    print(f"Previous hash: {previous_hashes[file]}")
                    print(f"Current hash:  {current_hashes[file]}")
                # Send email alert for modified files
                send_email_alert(modified_files)
            if deleted_files:
                print(f"Deleted files: {deleted_files}")
            if new_files:
                print(f"New files: {new_files}")
        else:
            print("No changes detected.")

        # Update the hash data and save the new state
        previous_hashes = current_hashes
        save_hashes(hash_file, current_hashes)

        # Wait for the next interval
        time.sleep(interval)


if __name__ == "__main__":
    if not os.path.exists(MONITOR_DIR):
        print(f"Error: Directory '{MONITOR_DIR}' does not exist.")
    else:
        monitor_files(MONITOR_DIR, HASH_FILE, MONITOR_INTERVAL)
