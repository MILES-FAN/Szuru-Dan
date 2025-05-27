# Szuru-Dan
A flask server that translate szuru api to danbooru style. (To let danbooru clients connect to szurubooru server)

## How to use
1. Clone this repository
   
    ```bash
    git clone https://github.com/MILES-FAN/Szuru-Dan.git
    ```

2. Install the requirements

    ```bash
    pip install -r requirements.txt
    ```

3. Edit the config file

    Edit the `config_.ini` file to set the url of the szurubooru server and the port of this api translator.

    Then rename the `config_.ini` to `config.ini`

    ```
    [API]
    # The url of the szurubooru server
    backend_url = http://127.0.0.1:8080/

    # The port of the api translator
    port = 9000

    # Enable reverse proxy mode 
    # Function: Image url will be translated to the url of the reverse proxy server
    # (Warning: If you are deploying this api translator on a cloud server, watch out for the bandwidth)
    reverse_proxy_mode = false

    # Enable performance timing logs (for debugging, most of the time you don't need it and the bottleneck is the szurubooru server)
    enable_timing_logs = false
    ```

4. Run the server

    ```bash
    python app.py
    ```

5. Now you can use your favorite danbooru clients to connect to the server.

## Supported API
- `/posts.json`
- `/posts/{id}.json`
- `/favorites.json`
- `/favorites/{id}.json`
- `/post_votes.json`
- `/users/{id}.json`
- `/profile.json`
- `/tags/autocomplete.json`

## Tested Clients

Android:
- [BooruHub(Flexbooru)](https://github.com/flexbooru/flexbooru)
- [Boorusama](https://github.com/khoadng/Boorusama)

IOS:
- [AnimeBoxes](https://www.animebox.es/)

PC:

- WIP.