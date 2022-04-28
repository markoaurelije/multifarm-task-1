# Coding Task Smart Contract Dev

## Task description
Please check out the vfat repository and how they integrated [AuroraSwap](https://github.com/vfat-tools/vfat-tools/blob/master/src/static/js/aurora_auroraswap.js):

Please write a simple endpoint, returning me the yearly APR for that pool (NEAR-WETH LP):

[VFAT TOOL HOMEPAGE](https://vfat.tools/aurora/auroraswap/)

## Realization
This implementation is just a very simple web endpoint returning the info as required above

## Build and deploy
## Prerequisites 

- python3
- pip

## Instructions

- clone this repos
- create new virtual environment: `python3 -m venv venv`
- install dependencies: `pip install -r requirements.txt`
- run: `python app.py`
- navigate to http address listed after run command, usually http://127.0.0.1:5000

####example output is like one below
> Pool Name: Aurora LPs  
Pool Symbol: Aurora-LP  
NEAR-WETH LP  
rewardsPerWeek:13745.454545454544  
APR: 28.52 %
