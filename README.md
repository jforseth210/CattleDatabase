# CattleDatabase
This is a program I designed in order to manage a beef herd. It is capable of keeping track of herd ancestry, events, ownership, and more. 

## How do I run it?
Please contact the author before using or modifying this code. 

(Note: These instructions are for Windows. If you are running Linux or Mac, the steps will be similar)
1. Download this project by clicking "Code", then "Download ZIP"
2. Extract the ZIP archive [How?](https://www.fonecope.com/unzip-files-windows-10.html)
3. Install [Python](https://www.python.org/)
4. Open this folder in a terminal, by going to the address bar and typing "cmd"
5. Enter the following commands 
```
source ./venv/Scripts/activate
pip install -r requirements.txt
python create_db.py
```
(If you get a command not found error, follow these steps: [https://www.makeuseof.com/python-windows-path/](https://www.makeuseof.com/python-windows-path/))

6. Start the application by running: 
`python main.py` (Don't close this window!)
7. Visit "http://localhost:5000/" in your web browser of choice. (Chrome, Firefox, Edge, etc.)
8. As long as the terminal is open, you'll be able to access the cattle database. 

## Extra Steps
Consider setting up the Python file to run at startup.

Determine your local IP to access the database from any device on the same network as the host computer. 


For further instructions on how to do this or help installing, please don't hesitate to create an issue. 

## License
ALL RIGHTS RESERVED
Please contact the author before using or modifying this code. 
