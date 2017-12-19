## Setting up python environment
```
virtualenv -p python3.5 env3.5
```

## Requirements
```
pip install requests
pip install bs4
```

### keywords
Create a `keywords.txt` file on this directory with a list of keywords to look for. Each keyword is on a new line.

### Sample usage
```
python crawlerExpand.py [URL] 10 50 lefolder
```
