from flask import Flask
from web3 import Web3
import requests

from constants import *

w3 = Web3(Web3.HTTPProvider('https://aurora-mainnet.infura.io/v3/b89f0b5d512b4bc9a5b8d7857a008b48'))
print(w3.isConnected())

app = Flask(__name__)


def get_erc20_token(token_address):
    erc20 = w3.eth.contract(address=token_address, abi=ERC20_ABI)
    calls = [erc20.functions.decimals(), erc20.functions.name(), erc20.functions.symbol(),
             erc20.functions.totalSupply()]
    [decimals, name, symbol, totalSupply] = map(lambda x: x.call(), calls)
    return {"decimals": decimals, "name": name, "symbol": symbol, "totalSupply": totalSupply}


def get_aurora_uni_pool(pool, pool_address, staking_address):
    calls = [
        pool.functions.decimals(), pool.functions.token0(), pool.functions.token1(), pool.functions.symbol(),
        pool.functions.name(), pool.functions.totalSupply(), pool.functions.balanceOf(staking_address)
    ]
    [decimals, token0, token1, symbol, name, totalSupply, stakedByChef] = map(lambda _pool: _pool.call(), calls)

    totalSupply = totalSupply / 10 ** decimals

    [reserve0, reserve1, *_] = pool.functions.getReserves().call()
    token0_erc20 = get_erc20_token(token0)
    token1_erc20 = get_erc20_token(token1)

    token0_quantity = reserve0 / 10 ** token0_erc20["decimals"]
    token1_quantity = reserve1 / 10 ** token1_erc20["decimals"]

    coingeckoToken0_id = [x for x in AuroraTokens if x["contract"] == token0][0]["id"]
    coingeckoRequest = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={coingeckoToken0_id}&vs_currencies=usd")
    token0_price = coingeckoRequest.json()[coingeckoToken0_id]["usd"]
    print(f"{token0_erc20['name']} price: {token0_price}")

    coingeckoToken1_id = [x for x in AuroraTokens if x["contract"] == token1][0]["id"]
    coingeckoRequest = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={coingeckoToken1_id}&vs_currencies=usd")
    token1_price = coingeckoRequest.json()[coingeckoToken1_id]["usd"]

    tvl = token0_quantity * token0_price + token1_quantity * token1_price
    TVL_price = tvl / totalSupply
    staked_tvl = stakedByChef / 10 ** decimals * TVL_price

    return {
        "symbol": symbol,
        "name": name,
        "staked_tvl": staked_tvl,
        "token0": token0_erc20["symbol"],
        "token1": token1_erc20["symbol"]
    }


def get_aurora_token(token_address, staking_address):
    pool = w3.eth.contract(address=token_address, abi=UNI_ABI)
    uniPool = get_aurora_uni_pool(pool, token_address, staking_address)
    return uniPool


def get_aurora_pool_info(chef_contract, chef_address, pool_index):
    poolInfo = chef_contract.functions.poolInfo(pool_index).call()
    [lpTokenAddress, allocPoints, *_] = poolInfo

    poolTokenDetails = get_aurora_token(lpTokenAddress, chef_address)
    return {
        "allocPoints": allocPoints,
        "staked_tvl": poolTokenDetails["staked_tvl"],
        "name": poolTokenDetails["name"],
        "symbol": poolTokenDetails["symbol"],
        "token0": poolTokenDetails["token0"],
        "token1": poolTokenDetails["token1"]
    }


def calculate_apr(pool_info, total_alloc_points, rewards_per_week, staked_tvl):
    poolRewardsPerWeek = pool_info["allocPoints"] / total_alloc_points * rewards_per_week
    r = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=borealis&vs_currencies=usd')
    rewardTokenPrice = r.json()["borealis"]["usd"]

    usdPerWeek = poolRewardsPerWeek * rewardTokenPrice
    weeklyAPR = usdPerWeek / staked_tvl * 100
    dailyAPR = weeklyAPR / 7
    yearlyAPR = weeklyAPR * 52

    return yearlyAPR


@app.route('/')
def get_apr():
    current_block = w3.eth.get_block_number()
    brl_chef = w3.eth.contract(address=BRL_CHEF_ADDR, abi=BRL_CHEF_ABI)
    multiplier = brl_chef.functions.getMultiplier(current_block, current_block + 1).call()

    rewardsPerWeek = brl_chef.functions.BRLPerBlock().call() / 1e18 * multiplier * 604800 / 1.1
    # poolCount = brl_chef.functions.poolLength().call()
    totalAllocPoints = brl_chef.functions.totalAllocPoint().call()

    # pool of interest (NEAR-WETH Uni LP) has pool_index = 1
    near_weth_poolIndex = 1
    poolInfo = get_aurora_pool_info(brl_chef, BRL_CHEF_ADDR, near_weth_poolIndex)

    apr = calculate_apr(poolInfo, totalAllocPoints, rewardsPerWeek, poolInfo["staked_tvl"])

    return "" \
           f"Pool Name: {poolInfo['name']}<br>\n" \
           f"Pool Symbol: {poolInfo['symbol']}<br>\n" \
           f"{poolInfo['token0']}-{poolInfo['token1']} LP<br>\n" \
           f"rewardsPerWeek:{rewardsPerWeek}<br>\n" \
           f"APR: {apr:.2f} %<br>\n"


if __name__ == '__main__':
    app.run()
    # print(get_apr())
