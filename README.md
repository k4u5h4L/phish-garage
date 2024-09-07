# Phish-Garage

A tool which would help you create phishing sites instantly from online websites.

## Tools used
- `Selenium` with the Chrome browser, to parse the DOM tree.
- `Requests` to download web assets.
- `Rich` to format terminal input and output prompts.

## How to install/run?
If you just want to use it, then go ahead to the releases tab in GitHub and download the executable for Linux (I have yet to compile it for Windows and Mac). The dependencies were bundled with `pyinstaller`. If you are using Windows or Mac, you can follow the below Development steps to get it running on your own OS.

## Prerequisites (for development)
- I have used `python 3.12`, although I reckon it should work other python distributions, as long as the path to the virtual env dependencies are set right, in the `main.spec` file.
- All dependencies in the `requirements.txt` file installed in the virtual environment.
- Bundle it using `pyinstaller` for your OS.
```bash
pyinstaller -F --paths=<path-to-venv>/site-packages main.py
# in my case, pyinstaller -F --paths=venv/lib/python3.12/site-packages main.py
```

You should then have the binary executable in the `dist/` folder. Simply run this.

# Note:
This project should be used only for educational purposes only. I am not liable for any consequences of you using this software for whatever it is you do.