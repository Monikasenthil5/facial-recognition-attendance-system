 
import cv2 
import face_recognition 
import sqlite3 
from datetime import datetime 
from io import BytesIO 
from PIL import Image 
import numpy as np 
import requests  # Import requests library for API calls 
 
# Connect to SQLite database 
conn = sqlite3.connect('database_name.db') 
cursor = conn.cursor() 
 
# Create a table to store attendance if it doesn't exist 
cursor.execute('''CREATE TABLE IF NOT EXISTS attendance 
                (id INTEGER,  
 
                name TEXT NOT NULL, 
                date DATE NOT NULL, 
                in_time TIME, 
                out_time TIME, 
                UNIQUE(id, date))''')  # Adding a UNIQUE constraint on (id, date) 
conn.commit() 
 
# Load known faces from the database 
cursor.execute('SELECT id, name, image FROM faces') 
known_faces = cursor.fetchall() 
 
# Initialize webcam 
video_capture = cv2.VideoCapture(0) 
 
attendance_recorded = {}  # Dictionary to track in-time and out-time for each 
recognized face 
 
# API endpoint for sheet.best to update Google Sheet 
api_url = 'api_url' 
 
while True: 
    # Capture frame-by-frame 
    ret, frame = video_capture.read() 
 
    # Convert the frame from BGR to RGB format (required by face_recognition library) 
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 
 
    # Find faces in the frame only when 'c' is pressed 
    if cv2.waitKey(1) & 0xFF == ord('c'): 
        face_locations = face_recognition.face_locations(rgb_frame) 
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations) 
 
        # Check if more than one face is detected 
        if len(face_locations) > 1: 
            message = "Faces cannot be processed. Multiple faces detected." 
            cv2.putText(frame, message, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, 
(0, 0, 255), 1) 
            cv2.imshow('Video', frame) 
            cv2.waitKey(5000)  # Display message for 5 seconds 
            continue  # Skip processing if multiple faces are detected 
 
        face_matched = False  # Flag to track if the face is matched with known faces 
 
        for face_encoding in face_encodings: 
            # Compare face encoding with known faces in the database 
            for id, name, image_blob in known_faces: 
                # Create a file-like object from the image blob data 
                image_file = BytesIO(image_blob) 
                image = Image.open(image_file) 
  
 
                # Convert the image to RGB format (required by face_recognition library) 
                image = image.convert('RGB') 
 
                known_face_encoding = 
face_recognition.face_encodings(np.array(image))[0] 
                match = face_recognition.compare_faces([known_face_encoding], 
face_encoding) 
 
                if match[0]: 
                    face_matched = True  # Set the flag to True if a match is found 
 
                    # Match found, check if attendance is already updated for this date 
                    current_date = datetime.now().strftime('%Y-%m-%d')  # Use ISO format 
for date 
 
                    cursor.execute('SELECT in_time, out_time FROM attendance WHERE 
id=? AND date=?', 
                                   (id, current_date)) 
                    existing_attendance = cursor.fetchone() 
 
                    if existing_attendance and existing_attendance[0] is not None and 
existing_attendance[ 
                        1] is not None: 
                        # Both in-time and out-time are not None, attendance already updated 
                        message = f"Attendance already updated for {name} on 
{current_date}." 
                        cv2.putText(frame, message, (30, 50), 
cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1) 
                        cv2.imshow('Video', frame) 
                        cv2.waitKey(5000)  # Display message for 5 seconds 
                    else: 
                        # Attendance not updated or partially updated, proceed with logging 
                        if existing_attendance is None: 
                            # Attendance not recorded for this date, record in-time 
                            current_time = datetime.now().strftime('%H:%M:%S') 
                            cursor.execute('INSERT INTO attendance (id, name, date, in_time) 
VALUES (?, ?, ?, ?)', 
                                           (id, name, current_date, current_time)) 
                            conn.commit() 
                            cv2.putText(frame, f"In-time logged for {name}.", (30, 50), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 1) 
                            cv2.imshow('Video', frame) 
                            cv2.waitKey(5000)  # Display message for 5 seconds 
                        else: 
                            # In-time recorded, update out-time 
                            current_time = datetime.now().strftime('%H:%M:%S') 
                            cursor.execute('UPDATE attendance SET out_time=? WHERE id=? 
AND date=?', 
                                           (current_time, id, current_date)) 
                            conn.commit() 
 
 
                            cv2.putText(frame, f"Out-time logged for {name}.", (30, 50), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 1) 
                            cv2.imshow('Video', frame) 
                            cv2.waitKey(5000)  # Display message for 5 seconds 
 
                            # Update Google Sheet with attendance data 
                            attendance_data = {'id': id, 'name': name, 'date': current_date, 
'in_time': existing_attendance[0], 
                                               'out_time': current_time} 
                            response = requests.post(api_url, data=attendance_data) 
                            print(response.json())  # Print API response 
 
                    break  # Exit inner loop if a match is found 
 
        if not face_matched: 
            # Face not recognized 
            cv2.putText(frame, "Face not recognized.", (30, 50), 
cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 1) 
            cv2.imshow('Video', frame) 
            cv2.waitKey(5000)  # Display message for 5 seconds 
 
    # Display the resulting frame 
    cv2.imshow('Video', frame) 
 
    # Exit loop if 'q' is pressed 
    if cv2.waitKey(1) & 0xFF == ord('q'): 
        break 
 
# Release video capture and close all windows 
video_capture.release() 
cv2.destroyAllWindows() 
 
# Close database connection 
conn.close() 
