@echo off
echo Instalando dependencias do NEXUS...
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
echo.
echo Se o microfone falhar por PyAudio, rode:
echo py -m pip install pipwin
echo pipwin install pyaudio
pause
