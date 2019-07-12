# connect-vpnbook
This tool helps connect you to [vpnbook](https://www.vpnbook.com/freevpn) freevpn service through OpenVPN.

## motivations
Vpnbook is a nice vpn provider, with 0 cost and a bunch of servers to open a connection. Some of them are configured especially for web surfing purposes, which higher up the speed and gives a better experience. They also says to have a low-profile logs keeping, as their [privacy policy](https://www.vpnbook.com/contact) tells us.
And as they also say, to achieve a maximum of active users on the vpn connections, the password is changed every week, and for automatic connections, some kind of script should be put in place.

## purposes and inspirations
This tool is initially for EDUCATION purposes only!
Anyway everything works just fine, but if you are looking for a shared script for your business for production environments, stay calm, but this project is not for you. That said, I really recommend a project written in shell script, with many more features and stable, called [vpnbook](https://github.com/HiMyNameIsIlNano/vpnbook).

## getting started
This implementation is for python version 3.7! Please read [installation](https://wwww.pyhton.org/downloads/).

### installing requirements
The first step is to install all the requirements, which are 3:
  - pexpect: interactive session with OpenVPN command;
  - bs4: HTML scrapping for image recognisation;
  - requests: high-level HTTP requests;

So on terminal run this:
```bash
pip3 install -r requirements.txt
```

**Note**: the command `pip3` generally only exists with systems with pip on python version 2, if is not your case the command `pip` is the right one.

And now, to properly create the vpn tunnel, we need the OpenVPN binary installed with all the dependencies. If you are a linux user, most probably your SO already have this installed. Anyway, to install it pick the right one for your system from the [community downloads](https://openvpn.net/community-downloads/). For the people who do not have it installed and use a package manager, just google it with your operating system and you will find a installation very quickly.

### starting connection
The main file is the `connect_vpn.py` and takes only one argument, which is the ovpn file to open the connection. This files are downloaded from vpnbook page. So
for example let's say we have downloaded the FR1 server from france and extracted the files to `fr1-srv` directory. To start a connection we type:

```bash
python3 connect_vpn.py fr1-srv/vpnbook-fr1-udp53.ovpn
```

If you have permission to open the connection everything will be fine. The permissions topic is discussed [here](#permissions).

#### but what vpn does?
Vpn aggregates security on layer 3 of OSI model, so the traffic will be first routed outside to some proxies of the vpn for then actually reach your target site `whatever.com`, that's why called as tunnels. Otherwise this tunnel does not makes connections anonymously, because in first place your internet provider already knows the IP of the vpn you contacted a time ago.

#### nice, but what the script is really doing?
If you want a vpn, privacy, security and all that stuff means something to you, so a script which will connects you to a free vpn must be considered too, it can be the one point failure, why not? So I will try to describe very non-technical how and what really happens.

First thing that must be said is that how OpenVPN works, and it's quite easy. You need a username, password and off course the ovpn file. Vpnbook provides all of that from their page, the ovpn files, the username that is default for everyone, and a password that changes every week. The detail here is the password, and besides it's volatile, the password is generated with image format, that means a image-to-text script is necessary. And nowadays image recognition is not something to wonder, there is something called optical character recognition, or just OCR that handles this problem very easy. In python there is the [Tesseract](https://github.com/madmaze/pytesseract) project to this, and it' is wonderful but the image with the password is provided in a way that confuses the recognition, and a better image treatment is necessary. So a simple search showed me this site [smallseotools](https://www.smallseotools.com/image-to-text-converter) that accepts URLs as input. Perfect! This was the major problem to be solved, the script is just an engineering about all that. And for sure it is intelligent enough to save the progress if some shit goes on, this can be time/bandwidth saving.

So...things to point out:
  - the script will avoid to open new connections, which is good because an attacker can use correlation to find who you are, and it's not difficult;
  - by default, once the image with password URL was retrieved, this one will be saved at `vpn_pwd.png` in case of error;
  - the image backup as said above will be ignored as cache if you you run the script again, and this is to:
    - avoid consuming requests for the image upload, which would be the only option;
    - guarantee to get always the active password;
  - by default, once the password text is recognised, this one will be saved at `vpn_pwd.txt`;
  - this password backup said above will be re-used by script as a password-in-memory feature, but if the authentication with vpnbook had failed with this cached password, it will be detected as that password is not active anymore and a job will be executed to get things working again;
  - this job operates in 3 simple process, retrieve fresh password URL, recognition to text format and interactive OpenVPN connection.
  - to retrieve the current password URL of the image, 1 request(GET) is made to the homepage of vpnbook, and from the response the URL is parsed;
  - to the recognition of the password, we need the image URL and 2 requests to smallseotools:
    - the first request is a HEAD to register some cookies and forge a normal user connection;
    - the last one is a POST with the parameters to the image, so the response contains the password embedded on HTML content;

For the first time use, successful execution, this script will always:
  - open 2 connections;
  - make 3 HTTP requests for 2 different websites;
  - make 1 file operation to save the password locally;
  - call the OpenVPN binary with privileged user;

#### ok, and what more can happen?
If the second process(recognition to text format) fails, more 1 request will be made to download the image with the password, but reusing the previously connection, and 1 file operation to store the image locally. So for the server perception, a user just entered the page and downloaded the image which is exactly what should happen on browser.

#### and when this happen what can I do?
With the image download on your machine, we human beings(at least I wish you are human) are able to recognize text in images, so you can be part of the script and execute process 2 by yourself putting the password in the file used as password-in-memory for the script, which is `vpn_pwd.txt` by default.

### permissions
To open the vpn tunnel some low-level stuff is executed by OpenVPN binary, as create virtual interfaces for the tunnel, add routes, make ssl negotiation using system certificates, so privileged access is required. As said by the OpenVPN creators, they build in a way that the root is dropped after initialization, which is good enough, but if you are paranoid you can for sure execute everything without root privileges, read [this](https://openvpn.net/community-resources/hardening-openvpn-security/). If this is what you want, you need also to change the source code to remove the `sudo` call to OpenVPN binary, located on `vpn_connector.py:27`.


## conclusion
As an education project it helped me to enter on networking word a little, understand how vpn tunnels work in practice.
Another improvement was to think in the most viable way to keep security, being very strict on the critical process, that is to obtain the password online.
A recommendation is to use proxychains with some good random proxies to avoid exposure and to limit correlation.     
