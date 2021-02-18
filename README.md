Scripts to interact with chat at minechat.dvmn.org.
This code was written for educational purposes for [Devman Async Python course](https://dvmn.org/modules/async-python)
## Install
```shell
pip install -r requirements.txt
```
## Usage
### Listen chat messages
All arguments are optional or can be provided via environmental variables. Also, default values can be used. 
```shell
python listen_chat.py --host minechat.dvmn.org --port 5000 --history minechat.txt
```
### Send a message
 * Register a new user and send a message. Your credentials will be saved into a file in a working directory. Default (or set via the environmental variables) nickname, host and port can be used.
    ```shell
    python send_to_chat.py --host minechat.dvmn.org --port 5000 --nickname Alice Hello!
    ```
* Authorize as an existing user and send a message

    ```shell
    python send_to_chat.py --host minechat.dvmn.org --port 5000 --token xxx --message Hello!
    ```
### Environment settings
* HOST - Hostname of a chat server.
* SEND_PORT - Port to use for sending messages.
* LISTEN_PORT - Port to use for listening.
* NICKNAME - Nickname of a new user.
* HISTORY_FILE - File where chat messages will be stored.

