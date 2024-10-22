# network-link-speeds
This script is used to fetch network link speeds for all hosts in a cluster.
Developed by Rushabh Jain (rushabh.jain@nutanix.com)


## Requirements

- Python 3.8 >= 
- Prism Element IPs in pe.csv
- Cluster Credentials (Prism Element)

## Setup

1. Download the script files on your system along with the requirements.

2. Create a virtual environment (optional but recommended):

    ```
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Install the required packages (if needed):

    ```bash
    pip3 install -r requirements.txt
    ```

## Usage



1. Run the script:

    ```
    python3 script_network.py
    ```



2. The script will fetch the result in result.csv.
