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
import subprocess
import os
import tempfile
import glob

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
        
        # Use webdriver-manager to automatically download matching chromedriver
        # This avoids version mismatch issues with system chromedriver
        print("Setting up Chrome driver with webdriver-manager...")
        try:
            # Get Chrome version for diagnostics
            if chrome_binary:
                try:
                    chrome_version_output = subprocess.run(
                        [chrome_binary, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if chrome_version_output.returncode == 0:
                        print(f"Chrome version: {chrome_version_output.stdout.strip()}")
                except:
                    pass
            
            # Use webdriver-manager to get matching chromedriver
            chromedriver_path = ChromeDriverManager().install()
            print(f"Using chromedriver: {chromedriver_path}")
            
            # Verify chromedriver is executable and check for missing libraries
            if not os.access(chromedriver_path, os.X_OK):
                os.chmod(chromedriver_path, 0o755)
                print("Made chromedriver executable")
            
            # Test if chromedriver can run (check for missing libraries)
            print("Testing chromedriver...")
            test_result = subprocess.run(
                [chromedriver_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if test_result.returncode != 0:
                print(f"ERROR: chromedriver cannot run!")
                print(f"stderr: {test_result.stderr}")
                print(f"stdout: {test_result.stdout}")
                print("\nThis usually means missing shared libraries.")
                print("Run this to check missing libraries:")
                print(f"  ldd {chromedriver_path}")
                raise Exception("chromedriver failed to start - missing dependencies")
            else:
                print(f"Chromedriver test passed: {test_result.stdout.strip()}")
            
            # Create service with log file for debugging
            log_file = tempfile.NamedTemporaryFile(delete=False, suffix='.log', prefix='chromedriver_')
            log_file.close()
            service = Service(chromedriver_path, log_path=log_file.name)
            
            self.__driver = webdriver.Chrome(service=service, options=chrome_options)
            self.__driver.set_window_size(width, height)
            print("Chrome driver initialized successfully")
            
        except Exception as e:
            print(f"\nError initializing Chrome driver: {e}")
            
            # Try to read the log file if it exists
            log_file_path = None
            try:
                if 'log_file' in locals():
                    log_file_path = log_file.name
                elif 'chromedriver_path' in locals():
                    # Try to find log file in temp directory
                    temp_logs = glob.glob('/tmp/chromedriver_*.log')
                    if temp_logs:
                        log_file_path = temp_logs[-1]  # Get most recent
                
                if log_file_path and os.path.exists(log_file_path):
                    print(f"\nChromedriver log ({log_file_path}):")
                    with open(log_file_path, 'r') as f:
                        log_content = f.read()
                        if log_content:
                            print(log_content)
                        else:
                            print("(log file is empty)")
            except Exception as ex:
                print(f"Could not read log file: {ex}")
            
            # Check what libraries chromedriver needs
            if 'chromedriver_path' in locals():
                print("\nChecking chromedriver dependencies...")
                try:
                    ldd_result = subprocess.run(
                        ["ldd", chromedriver_path],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if ldd_result.returncode == 0:
                        missing_libs = [line for line in ldd_result.stdout.split('\n') if 'not found' in line]
                        if missing_libs:
                            print("Missing libraries detected:")
                            for lib in missing_libs:
                                print(f"  {lib.strip()}")
                        else:
                            print("All libraries found. Try running chromedriver directly:")
                            print(f"  {chromedriver_path} --version")
                except Exception as ex:
                    print(f"Could not check dependencies: {ex}")
            
            print("\nTroubleshooting steps:")
            if chrome_binary:
                print("\n1. Check if Chrome/Chromium is working:")
                print(f"   {chrome_binary} --version")
            else:
                print("\n1. Chrome/Chromium not found. Install it first:")
                print("   apt-get update && apt-get install -y chromium-browser")
            print("\n2. Install ALL required dependencies:")
            print("   apt-get update && apt-get install -y \\")
            print("     chromium-browser \\")
            print("     libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 \\")
            print("     libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \\")
            print("     libgbm1 libasound2 libxss1 libgtk-3-0")
            print("\n3. Check chromedriver dependencies:")
            print(f"   ldd {chromedriver_path}")
            print("\n4. Clear webdriver-manager cache and reinstall:")
            print("   rm -rf ~/.wdm")
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
