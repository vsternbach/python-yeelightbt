import subprocess
import shutil
import os

service_file = './yeelightbtle.service'

# Copy the service file to the systemd directory
destination = '/etc/systemd/system/yeelightbtle.service'
shutil.copyfile(service_file, destination)

# Reload systemd to recognize the new service
subprocess.call(['systemctl', 'daemon-reload'])

# Enable and start the service
subprocess.call(['systemctl', 'enable', 'yeelightbtle.service'])
subprocess.call(['systemctl', 'status', 'yeelightbtle.service'])
subprocess.call(['systemctl', 'start', 'yeelightbtle.service'])
