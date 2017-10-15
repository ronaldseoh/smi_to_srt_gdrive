# smi_to_srt_gdrive

`smi_to_srt_gdrive` is a Python script that allows the automatic conversion of SMI subtitle files on Google Drive to SRT subtitle files.

This repository includes works by Moonchang Chae (http://egloos.zum.com/mcchae/v/10763080) and taylor224 (https://gist.github.com/taylor224/4c80ad3d047af48aa4a0cc64baee22aa). (Please check [`convert.py`](convert.py) for details.)

## Usage

This script uses [`pydrive`](https://github.com/googledrive/PyDrive) package. Install `pydrive` using `pip install pydrive` first. **NOTE: This script does not work with Python 2.**

You also need to supply your own OAUTH client ID and secrets. You can do this at <https://console.cloud.google.com>. Put `client_secrets.json` in the directory where `smi_to_srt_gdrive.py` is in.

After that, type `python smi_to_srt_gdrive.py` in the terminal and follow the instructions.

Just in case you would like to use this script along with other `pydrive`-based Python applications, you can also use this script by importing `GDriveSmiToSrtConverter` directly into your code and supplying your own `GoogleDrive` and/or `target_files` object.

## License

`smi_to_srt_gdrive` is licensed under GPLv3 license. Please check [`LICENSE`](LICENSE).
