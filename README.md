# CattleDatabase
This is a program I designed in order to manage my beef herd. It is capable of keeping track of herd ancestry, events like branding and shipping, ownership, transactions, and more. 

## How does it work?
You choose a "host computer" to run your database. It stores the herd information locally on your computer and makes them accessible via a web interface. This can be accessed from the host computer even without an internet connection. When connected, it is available to any device on your home internet or (optionally, if your connection supports it) from anywhere with internet. 

## How do I run it?
I'm working on an installer, but it's not quite ready yet. Hold tight! (Or if you really can't wait, contact me for manual installation instructions)

Once it's finished, you'll be asked a few simple questions:
```
The database hasn't been created yet. Would you like to:")
1) Create a new database
2) Import an existing database"
```
If this is your first time installing, type "1" (without the quotes) and press enter. If you want to copy over an existing installation, find the "cattle.db" file from your old installation and copy it into the new folder.

The same applies for creating a configuration file. To import an existing config, just copy "config.json"

For online mode, read the security disclaimer below. It is more convienient, but may be less secure. When in doubt, contact me or consult your local "tech wiz".

If you choose online mode and are running Windows, you may be prompted to install UPNP Wizard. Please do so. You don't need to do anything once the program is installed. CattleDB uses it in the background to automatically configure your network connection to allow for online access. 

## Is it secure?
Short answer: No, probably not. I'm still an amatuer programmer, and there are probably a few security holes I haven't noticed.

You can greatly improve your security by leaving online mode disabled. This effectively makes it impossible to "hack" your records without access to your network. 

AS OF 6/1/21, IF YOU CHOOSE TO MAKE YOUR RECORDS AVAILABLE ONLINE, THEY ARE EDITABLE BY ANYONE WHO KNOWS THE ADDRESS. I
WILL LIKELY ADD A LOGIN FORM IN THE VERY NEAR FUTURE.

There are few security concerns associated with the way this program is designed:
1) Anyone with access to the host computer (and some technical skills) can access the database, either by modifying the username/password hash stored in config.json or by accessing cattle.db directly. KEEP YOUR HOST COMPUTER SECURE
2) Logins are (CURRENTLY NOT IMPLEMENTED, BUT WHEN IMPLEMENTED WILL BE) transmitted in plain-text. This means that anyone between the device you're accessing your records from and your host computer could potentially read your password. For example, any cell carrier, internet service provider, or wifi network between you and your host computer, could potentially see your password. USE A UNIQUE PASSWORD, AND ONLY ACCESS YOUR RECORDS ON TRUSTED NETWORKS. 

In short, this program is secure enough to dissuade the casual snooper, however it would be fairly easy for a dedicated attacker to gain access when online mode is enabled.

## Disclaimer
I am a teenager. I'm largely self-taught. While I want this program to be useful to you, I am in no way prepared to be responsible for writing software that safely, securely, or reliably manages your herd. 
USE AT YOUR OWN RISK.
THIS PROGRAM COMES WITH ABSOLUTELY NO WARRANTY.

## License
ALL RIGHTS RESERVED
Please contact me before using or modifying my code. I would be happy to allow you or even help you use or modify it, but CONTACT ME before doing so. Thank you!
