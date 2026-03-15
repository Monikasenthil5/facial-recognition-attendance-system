import cv2 
import os 
import face_recognition 
import sqlite3 
 
# Create a folder to store captured faces 
output_folder = 'captured_faces' 
os.makedirs(output_folder, exist_ok=True) 
 
# Initialize webcam 
video_capture = cv2.VideoCapture(0) 
 
# Connect to SQLite database 
conn = sqlite3.connect('database_name.db') 
cursor = conn.cursor() 
 
# Create a table to store face data if it doesn't exist 
cursor.execute('''CREATE TABLE IF NOT EXISTS faces 
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                name TEXT NOT NULL, 
                image BLOB NOT NULL)''') 
conn.commit() 
 
while True: 
    # Capture frame-by-frame 
    ret, frame = video_capture.read() 
 
    # Display the captured frame 
    cv2.imshow('Capture', frame) 
 
    # Find faces in the frame 
    face_locations = face_recognition.face_locations(frame) 
 
    # Check if multiple faces are detected 
    if len(face_locations) > 1: 
        message = "Faces cannot be scanned. Multiple faces detected." 
        cv2.putText(frame, message, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 
255), 2) 
        cv2.imshow('Capture', frame) 
        cv2.waitKey(5000)  # Display message for 5 seconds 
        continue  # Skip processing if multiple faces are detected 
 
    # Wait for 'c' key to capture a face 
    if cv2.waitKey(1) & 0xFF == ord('c'): 
        for face_location in face_locations: 
            # Extract the face from the frame 
 
            top, right, bottom, left = face_location 
            face_image = frame[top:bottom, left:right] 
 
            # Close OpenCV window after capturing face 
            cv2.destroyAllWindows() 
 
            # Ask user for name 
            name = input("Enter name: ") 
 
            # Save the captured face as a JPG file 
            file_name = f'face_{len(os.listdir(output_folder)) + 1}.jpg' 
            cv2.imwrite(os.path.join(output_folder, file_name), face_image) 
 
            # Save face data to database 
            with open(os.path.join(output_folder, file_name), 'rb') as f: 
                image_blob = f.read() 
                cursor.execute('INSERT INTO faces (name, image) VALUES (?, ?)', 
                               (name, image_blob)) 
                conn.commit() 
 
            print(f"Face captured and saved as {file_name}, Name: {name}") 
 
    # Exit loop if 'q' is pressed 
    elif cv2.waitKey(1) & 0xFF == ord('q'): 
        break 
 
# Release video capture 
video_capture.release() 
 
# Close database connection 
conn.close() 
