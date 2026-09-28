# Onion Downloader

A Python utility for downloading files from Tor onion services (.onion URLs).

## Description

Onion Downloader automates the process of downloading files from `.onion` addresses by automatically starting a Tor service and routing HTTP/HTTPS requests through the Tor SOCKS proxy. No manual Tor configuration required.

## Requirements

- Python 3.6+
- Tor installed and available in PATH

## Installation

Install dependencies using pip:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Download

Download a file from an onion address:

```bash
python3 onion_download.py example.onion
```

### Specify Output File

Save the downloaded file with a custom name:

```bash
python3 onion_download.py https://example.onion/file.zip -o myfile.zip
```


## Features

- Automatic Tor startup and management
- SOCKS5 proxy routing through Tor
- Download progress tracking
- Proper cleanup on interruption
- Custom output filename support

## License

MIT