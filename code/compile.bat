pyinstaller --onefile the_only_one.py
rd /s /q __pycache__
rd /s /q build
move dist\the_only_one.exe ..
rd /s /q dist
del the_only_one.spec