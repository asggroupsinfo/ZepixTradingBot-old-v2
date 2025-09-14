@echo off
echo Adding Windows Firewall rule for port 80...
netsh advfirewall firewall add rule name="Zepix Trading Bot HTTP" dir=in action=allow protocol=TCP localport=80
echo Firewall rule added successfully!
pause