# smi_to_srt_gdrive

`smi_to_srt_gdrive` is a Python script that allows the automatic conversion of smi subtitle files on Google Drive to srt subtitle files.

This repository includes works by Moonchang Chae (http://egloos.zum.com/mcchae/v/10763080) and taylor224 (https://gist.github.com/taylor224/4c80ad3d047af48aa4a0cc64baee22aa). (Please check [`convert.py`](convert.py) for details.)

## Usage

You need to supply your own OAUTH client ID and secrets first. You can do this at <https://console.cloud.google.com>. Put `client_secrets.json` in the directory where `smi_to_srt_gdrive.py` is in.

After that, type `python3 smi_to_srt_gdrive.py` in the terminal and follow the instructions.

## License

`smi_to_srt_gdrive` is licensed under GPLv3 license. Please check [`LICENSE`](LICENSE).
