from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.core.window import Window
from kivy.uix.camera import Camera
from kivy.clock import Clock
import pymongo
from pymongo import MongoClient
import datetime
from pyzbar.pyzbar import decode
from PIL import Image as PILImage
from io import BytesIO
import os
import tempfile

# MongoDB connection
client = MongoClient('mongodb+srv://sayalu00:wnQJnnebRCSvfNsR@cluster0.on3ubv6.mongodb.net/')
db = client['attendance_database']
collection = db['attendance_entries']

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        
        # Layouts
        layout = BoxLayout(orientation='vertical')
        
        # Header
        header = BoxLayout(size_hint=(1, None), height=Window.height * 0.2, padding=[10, 10])
        
        header_content = BoxLayout(orientation='horizontal', size_hint=(1, 1))
        header_label = Label(text="DV's Fitness App", font_size=55, bold=True, color=[1, 1, 1, 1])  # White text color
        header_content.add_widget(header_label)
        
        header.add_widget(header_content)
        
        layout.add_widget(header)
        
        # Central Image
        center_image = Image(source='logo.png', size_hint=(1, 0.5))  # Reduce central image size
        layout.add_widget(center_image)
        
        # Buttons
        btn_layout = BoxLayout(orientation='vertical', size_hint_y=0.3, padding=[20, 50])
        self.scan_button = Button(text='Mark Attendance for Today', font_size=33, size_hint_y=None, height=Window.height * 0.1,
                                  on_press=self.open_camera)
        self.view_button = Button(text='View Past Attendance', font_size=33, size_hint_y=None, height=Window.height * 0.1,
                                  on_press=self.view_entries)
        btn_layout.add_widget(self.scan_button)
        btn_layout.add_widget(self.view_button)
        
        layout.add_widget(btn_layout)
        
        self.add_widget(layout)
        
        self.camera = Camera(play=False)  # Initialize camera widget (not playing initially)
        self.popup = Popup(title='Scan QR Code', content=self.camera, size_hint=(0.9, 0.9))
        self.entry_saved = False  # Flag to track if an entry has been saved
    
    def open_camera(self, instance):
        # Open camera when the button is pressed
        self.camera.play = True
        self.popup.open()

        def on_complete(dt):
            # Check for QR code detection
            if self.camera.texture is not None and not self.entry_saved:  # Check if entry already saved
                temp_file = os.path.join(tempfile.gettempdir(), 'camera_image.png')
                self.camera.export_to_png(temp_file)

                with open(temp_file, 'rb') as f:
                    buf = BytesIO(f.read())

                pil_img = PILImage.open(buf)
                qr_codes = decode(pil_img)
                if qr_codes:
                    qr_data = qr_codes[0].data.decode('utf-8')
                    print(qr_data)
                    if qr_data=="Dava fitness is very fun says everyone ":
                        self.store_entry(qr_data)
                        self.camera.play = False  # Disable camera
                        self.popup.dismiss()  # Close popup
                        os.remove(temp_file)  # Clean up temporary file
                        self.entry_saved = True  # Set flag to true after saving entry
                        self.show_success_popup()  # Show success popup
                        self.manager.current = 'main'  # Return to main screen after storing entry
                    else:
                        self.camera.play = False  # Disable camera
                        self.popup.dismiss()  # Close popup
                        os.remove(temp_file)  # Clean up temporary file
                        self.entry_saved = True  # Set flag to true after saving entry
                        self.show_fail_popup()  # Show success popup
                        self.manager.current = 'main'
        Clock.schedule_interval(on_complete, 1.0 / 30.0)
    
    def store_entry(self, qr_data):
        # Store entry in MongoDB with a default username
        entry = {
            'name': 'Sahil Kale',  # Default username
            'qr_content': qr_data,
            'timestamp': datetime.datetime.now()
        }
        collection.insert_one(entry)
        print(f"Stored entry: {entry}")
    
    def show_success_popup(self):
        # Popup to show success message
        success_popup = Popup(title='Success', content=Label(text='Attendance marked. Thank you!'),
                              size_hint=(None, None), size=(400, 400))
        success_popup.open()
    
    def show_fail_popup(self):
        # Popup to show success message
        fail_popup = Popup(title='Failure', content=Label(text='Attendance not marked. Wrong QR!'),
                              size_hint=(None, None), size=(400, 400))
        fail_popup.open()
    
    def view_entries(self, instance):
        # Function to fetch and display recent 5 entries with formatted date and time
        entries = collection.find().sort('timestamp', pymongo.DESCENDING).limit(5)
        content = BoxLayout(orientation='vertical', padding=[10])
        
        for entry in entries:
            formatted_date = entry['timestamp'].strftime('%d %B %Y')
            formatted_time = entry['timestamp'].strftime('%I:%M %p')
            entry_text = f"Name: {entry['name']} Datetime:{formatted_date} {formatted_time} Duration: 1 hour"
            entry_label = Label(text=entry_text, size_hint_y=None, height=Window.height * 0.1,
                                text_size=(None, None), halign='left', valign='middle', font_size=18)
            entry_label.bind(size=entry_label.setter('text_size'))
            content.add_widget(entry_label)
        
        popup = Popup(title='Past 5 Attendace Entries', content=content, size_hint=(0.8, 0.8))
        popup.open()

class AttendanceApp(App):
    def build(self):
        sm = ScreenManager()
        main_screen = MainScreen(name='main')
        sm.add_widget(main_screen)
        return sm

if __name__ == '__main__':
    AttendanceApp().run()
