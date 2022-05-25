from brownie import config, network, interface
from scripts.helpful_scripts import get_account
from scripts.get_weth import get_weth
from web3 import Web3
import time

amount = Web3.toWei(0.1, "ether")


def main():
    account = get_account()
    erc20_address = config["networks"][network.show_active()]["weth_token"]
    if network.show_active() in ["mainnet-fork"]:
        get_weth()
    # ANI
    # Address
    lending_pool = get_lending_pool()
    # Approve sending out ERC20 Token
    approve_erc20(amount, lending_pool.address, erc20_address, account)
    print("Depositing...")
    tx = lending_pool.deposit(
        erc20_address, amount, account.address, 0, {"from": account}
    )
    tx.wait(1)
    time.sleep(1)
    print("Deposited!")
    # how much?
    borrowable_eth, total_debt = get_borrowable_data(lending_pool, account)
    # DAI in terms of etherum
    # Change price feed address depending on what network
    dai_eth_price = get_asset_price(
        config["networks"][network.show_active()]["dai_eth_price_feed"]
    )
    amount_dai_to_borrow = (1 / dai_eth_price) * (borrowable_eth * 0.95)
    # borrowable_eth -> borrowable_dai * 95%
    converted_to_wei = Web3.toWei(amount_dai_to_borrow, "ether")
    print(
        f"We are going to borrow {amount_dai_to_borrow} DAI, {converted_to_wei} in Wei"
    )
    dai_address = config["networks"][network.show_active()]["dai_token"]
    borrow_tx = lending_pool.borrow(
        dai_address, converted_to_wei, 1, 0, account.address, {"from": account}
    )
    borrow_tx.wait(1)
    time.sleep(1)
    print("We just borrowed some Dai!")
    get_borrowable_data(lending_pool, account)
    #when designing the repay function, be sure to note that interest are acumulated on
    #the money borrowed
    repay_all(amount, lending_pool, account)
    print("You just deposited, borrowed, and repayed with AAVE, Brownie and ChainLink")


def repay_all(amount, lending_pool, account):
    approve_erc20(
        Web3.toWei(amount, "ether"),
        lending_pool,
        config["networks"][network.show_active()]["dai_token"],
        account,
    )
    repay_tx = lending_pool.repay(
        config["networks"][network.show_active()]["dai_token"],
        amount,
        1,
        account.address,
        {"from": account},
    )
    repay_tx.wait(1)
    time.sleep(1)
    print("Repayed!")


def get_asset_price(price_feed_address):
    # ABI
    # ADDRESS
    dai_eth_price_feed = interface.AggregatorV3Interface(price_feed_address)
    latest_price = dai_eth_price_feed.latestRoundData()[1]
    converted_latest_price = Web3.fromWei(latest_price, "ether")
    print(f"The DAI/ETH price is {converted_latest_price}")
    return float(converted_latest_price)


def get_borrowable_data(lending_pool, account):
    (
        total_collateral_eth,
        total_debt_eth,
        available_borrow_eth,
        current_liquidation_threshold,
        ltv,
        health_factor,
    ) = lending_pool.getUserAccountData(account.address)
    available_borrow_eth = convertToEther(available_borrow_eth)
    total_collateral_eth = convertToEther(total_collateral_eth)
    total_debt_eth = convertToEther(total_debt_eth)
    print(f"You have {total_collateral_eth} worth of ETH deposited.")
    print(f"You have {total_debt_eth} worth of ETH borrowed.")
    print(f"You can borrowed {available_borrow_eth} worth of ETH.")
    return (float(available_borrow_eth), float(total_debt_eth))


def convertToEther(valueToConvert):
    return Web3.fromWei(valueToConvert, "ether")


def approve_erc20(amount, spender, erc20_address, account):
    # Approves any ERC20 token
    print("Approving ERC20 token...")
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)
    time.sleep(1)
    print("Approved!")
    return tx
    # ABI
    # ADDRESS


def get_lending_pool():
    # ABI
    # Address
    lending_pool_addresses_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addresses_provider"]
    )
    lending_pool_address = lending_pool_addresses_provider.getLendingPool()
    # ABI
    # ADDRESS
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool
