#
# This demo will join a Daily meeting and stream live Chrome browser frames
# at the specified framerate using a virtual camera device.
#
# Usage: python3 videotest.py -m MEETING_URL -u URL -f FRAME_RATE
#

import argparse
import time
import threading
import io
import sys
import shutil

from daily import *
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class SendBrowserApp:
    def __init__(self, url, framerate, width=1920, height=1080):
        self.__url = url
        self.__framerate = framerate
        self.__width = width
        self.__height = height

        # Set up Chrome with Selenium
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"--window-size={width},{height}")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-extensions")
        # Run in headless mode for Vast AI
        chrome_options.add_argument("--headless=new")
        
        # Check if Chrome/Chromium is installed
        chrome_paths = [
            shutil.which("google-chrome"),
            shutil.which("google-chrome-stable"),
            shutil.which("chromium"),
            shutil.which("chromium-browser"),
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
        ]
        chrome_binary = next((path for path in chrome_paths if path), None)
        
        if chrome_binary:
            chrome_options.binary_location = chrome_binary
            print(f"Using Chrome binary: {chrome_binary}")
        else:
            print("Warning: Chrome/Chromium not found in PATH. Trying default locations...")
        
        # Try to find system chromedriver first (matches installed Chrome/Chromium)
        chromedriver_paths = [
            shutil.which("chromedriver"),
            "/usr/bin/chromedriver",
            "/usr/lib/chromium-browser/chromedriver",
            "/snap/chromium/current/usr/lib/chromium-browser/chromedriver",
        ]
        chromedriver_binary = next((path for path in chromedriver_paths if path), None)
        
        try:
            if chromedriver_binary:
                print(f"Using system chromedriver: {chromedriver_binary}")
                service = Service(chromedriver_binary)
                self.__driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                # Fall back to webdriver-manager
                print("System chromedriver not found, using webdriver-manager...")
                service = Service(ChromeDriverManager().install())
                self.__driver = webdriver.Chrome(service=service, options=chrome_options)
            
            self.__driver.set_window_size(width, height)
            print("Chrome driver initialized successfully")
        except Exception as e:
            print(f"\nError initializing Chrome driver: {e}")
            print("\nTrying to install missing dependencies...")
            print("Run these commands to fix:")
            print("\n1. Install Chromium and chromedriver:")
            print("   apt-get update && apt-get install -y chromium-browser chromium-chromedriver")
            print("\n2. If chromedriver is missing dependencies, install them:")
            print("   apt-get install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2")
            print("\n3. Make chromedriver executable:")
            print("   chmod +x /usr/bin/chromedriver")
            print("\n4. Then reinstall webdriver-manager:")
            print("   pip install --upgrade webdriver-manager")
            sys.exit(1)
        
        if url:
            print(f"Opening URL: {url}")
            self.__driver.get(url)
        else:
            print("Opening blank page")
            self.__driver.get("about:blank")
        
        # Give browser time to load
        time.sleep(2)

        # Create camera device with browser dimensions
        self.__camera = Daily.create_camera_device(
            "my-camera", width=width, height=height, color_format="RGB"
        )

        self.__client = CallClient()

        self.__client.update_subscription_profiles(
            {"base": {"camera": "unsubscribed", "microphone": "unsubscribed"}}
        )

        self.__app_quit = False
        self.__app_error = None

        self.__start_event = threading.Event()
        self.__thread = threading.Thread(target=self.send_frames)
        self.__thread.start()

    def on_joined(self, data, error):
        if error:
            print(f"Unable to join meeting: {error}")
            self.__app_error = error
        self.__start_event.set()

    def run(self, meeting_url):
        self.__client.join(
            meeting_url,
            client_settings={
                "inputs": {
                    "camera": {"isEnabled": True, "settings": {"deviceId": "my-camera"}},
                    "microphone": False,
                }
            },
            completion=self.on_joined,
        )
        self.__thread.join()

    def leave(self):
        self.__app_quit = True
        self.__thread.join()
        if self.__driver:
            self.__driver.quit()
        self.__client.leave()
        self.__client.release()

    def send_frames(self):
        self.__start_event.wait()

        if self.__app_error:
            print(f"Unable to send frames!")
            return

        sleep_time = 1.0 / self.__framerate

        while not self.__app_quit:
            try:
                # Capture screenshot from browser
                screenshot = self.__driver.get_screenshot_as_png()
                
                # Convert to PIL Image
                image = Image.open(io.BytesIO(screenshot))
                
                # Resize if needed to match camera dimensions
                if image.size != (self.__width, self.__height):
                    image = image.resize((self.__width, self.__height), Image.Resampling.LANCZOS)
                
                # Convert to RGB if needed
                if image.mode != "RGB":
                    image = image.convert("RGB")
                
                # Convert to bytes and send
                image_bytes = image.tobytes()
                self.__camera.write_frame(image_bytes)
                
            except Exception as e:
                print(f"Error capturing frame: {e}")
            
            time.sleep(sleep_time)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--meeting", required=True, help="Daily meeting URL")
    parser.add_argument("-u", "--url", default="", help="URL to open in browser (default: blank page)")
    parser.add_argument("-f", "--framerate", type=int, default=30, help="Framerate (default: 30)")
    parser.add_argument("--width", type=int, default=1920, help="Browser width (default: 1920)")
    parser.add_argument("--height", type=int, default=1080, help="Browser height (default: 1080)")
    args = parser.parse_args()

    Daily.init()

    app = SendBrowserApp(args.url, args.framerate, args.width, args.height)

    try:
        app.run(args.meeting)
    except KeyboardInterrupt:
        print("Ctrl-C detected. Exiting!")
    finally:
        app.leave()


if __name__ == "__main__":
    main()
