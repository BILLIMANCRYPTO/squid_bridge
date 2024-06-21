import random
import logging
import requests
import time
import secrets
from settings import MIN_DELAY, MAX_DELAY, GAS_PRICE, MIN_BALANCE, MAX_BALANCE, RPC_URL, chainId_sent, chain_ids, RANDOM_RECIVE, chain_recive, from_token, to_token, slippage
from datetime import datetime
from web3 import Web3
from eth_account import Account
from colorama import init, Fore
import json

# Инициализация colorama
init(autoreset=True)

# Инициализация Web3
web3 = Web3(Web3.HTTPProvider(RPC_URL))

# Загрузка ABI контракта
with open('abi.json', 'r') as abi_file:
    contract_abi = json.load(abi_file)

# Инициализация контракта
contract_address = '0xce16F69375520ab01377ce7B88f5BA8C48F8D666'
contract = web3.eth.contract(address=contract_address, abi=contract_abi)

# Загрузка приватных ключей из файла
with open('keys.txt', 'r') as file:
    private_keys = [line.strip() for line in file]

def cryptographic_shuffle(lst):
    for i in range(len(lst) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        lst[i], lst[j] = lst[j], lst[i]

# Перемешивание списка приватных ключей
cryptographic_shuffle(private_keys)

# Генерация кошельков из приватных ключей
wallets = [Account.from_key(private_key).address for private_key in private_keys]

# Переменная для использования случайного выбора цепочки
use_random_chain = RANDOM_RECIVE

# Функция для получения текущей цены газа через RPC
def get_current_gas_price():
    return web3.eth.gas_price

# Функция для получения текущей базовой комиссии через RPC
def get_current_base_fee():
    latest_block = web3.eth.get_block('latest')
    return latest_block['baseFeePerGas']

# Функция для проверки и ожидания снижения цены газа
def wait_for_gas_price_below(threshold_gwei):
    while True:
        gas_price = get_current_gas_price()
        gas_price_gwei = Web3.from_wei(gas_price, 'gwei')
        if gas_price_gwei <= threshold_gwei:
            break
        print(f'{gas_price_gwei:.2f} GWEI > {threshold_gwei} GWEI')
        time.sleep(60)  # Подождать 60 секунд перед следующей проверкой

# Функция для отправки запроса и выполнения транзакции
def squid_bridge(wallet_address, private_key, web3, i):
    balance = web3.eth.get_balance(wallet_address)
    if balance <= 0:
        logging.error(f"Insufficient balance in wallet {wallet_address}")
        return None

    # Вычисление суммы в диапазоне от MIN_BALANCE до MAX_BALANCE баланса
    min_amount = balance * MIN_BALANCE
    max_amount = balance * MAX_BALANCE
    amount = random.uniform(min_amount, max_amount)
    amount_str = str(int(amount))  # Преобразование суммы в целое число и строку

    # Выбор destinationChainId и его названия
    if use_random_chain:
        destination_chain_id, chain_name_recive = random.choice(list(chain_ids.items()))
    else:
        destination_chain_id, chain_name_recive = next(iter(chain_recive.items()))  # Использовать первую цепочку в списке

    url = f"https://api.squidrouter.com/v1/route?fromChain={chainId_sent}&fromToken={from_token}&fromAddress={wallet_address}&fromAmount={amount_str}&toChain={destination_chain_id}&toToken={to_token}&toAddress={wallet_address}&quoteOnly=false&slippage={slippage}&enableExpress=true"

    headers = {'Content-Type': 'application/json'}

    # Максимальное количество попыток
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers)
            response_data = response.json()

            if response.status_code != 200:
                logging.error(f"Failed to fetch data from API: {response.text}")
                if response.status_code in [502, 504]:
                    logging.info(f"Retrying... ({attempt + 1}/{max_retries})")
                    time.sleep(2 ** attempt)  # Экспоненциальное увеличение времени ожидания
                    continue
                return None

            try:
                # Извлекаем значение 'data'
                data = response_data.get('route', {}).get('transactionRequest', {}).get('data', None)
                sent_value = int(response_data.get('route', {}).get('transactionRequest', {}).get('value', None))
                gas_limit_squid = int(response_data.get('route', {}).get('transactionRequest', {}).get('gasLimit', None))
                to_amount = int(response_data.get('route', {}).get('estimate', {}).get('toAmount', None))
                # Извлекаем первое значение 'chainName'
                chain_names = []
                from_chain = response_data.get('route', {}).get('estimate', {}).get('route', {}).get('fromChain', [])
                to_chain = response_data.get('route', {}).get('estimate', {}).get('route', {}).get('toChain', [])

                for swap in from_chain:
                    chain_name = swap.get('dex', {}).get('chainName', None)
                    if chain_name:
                        chain_names.append(chain_name)

                for swap in to_chain:
                    chain_name_to = swap.get('dex', {}).get('chainName', None)
                    if chain_name_to:
                        chain_names.append(chain_name_to)

                if chain_names:
                    first_chain_name = chain_names[0]
                else:
                    print("ошибка парса")
                    first_chain_name = "Неизвестно"

                gas_price = get_current_gas_price()
                base_fee = get_current_base_fee()
                max_fee_per_gas = base_fee + Web3.to_wei(2, 'gwei')
                max_priority_fee_per_gas = Web3.to_wei(2, 'gwei')

                # Проверка цены газа и ожидание, если она выше порогового значения
                wait_for_gas_price_below(GAS_PRICE)

                # Получение текущей даты и времени
                current_time = datetime.now()

                print(
                    f'{current_time.date()} {current_time.time()} | [{i}/{len(wallets)}] | {wallet_address} | Squid Router | Sent {sent_value / 10 ** 18} ETH from {first_chain_name} to {chain_name_recive}, Recive {to_amount / 10 ** 18} -  ETH in {chain_name_recive}')

                try:
                    # Определение gasLimit
                    gas_limit1 = web3.eth.estimateGas({
                        'from': wallet_address,
                        'to': contract_address,
                        'value': sent_value,
                        'data': data
                    })

                    tx_params = {
                        'nonce': web3.eth.get_transaction_count(wallet_address),
                        'maxFeePerGas': max_fee_per_gas,
                        'maxPriorityFeePerGas': max_priority_fee_per_gas,
                        'gas': gas_limit_squid,
                        'to': contract_address,
                        'value': sent_value,
                        'data': data,
                        'chainId': chainId_sent,  # ID сети ETH
                    }

                    signed_tx = web3.eth.account.sign_transaction(tx_params, private_key)
                    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

                    # Ожидание подтверждения транзакции
                    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
                    if tx_receipt.status == 1:
                        # Получение текущего баланса эфира на кошельке
                        balance_after_tx = web3.eth.get_balance(wallet_address)

                        print(
                            f'{current_time.date()} {current_time.time()} | [{i}/{len(wallets)}] | {wallet_address} | Squid Router | Wallet Balance in {first_chain_name}: {web3.from_wei(balance_after_tx, "ether")} ETH')

                        print(
                            Fore.GREEN + f'{current_time.date()} {current_time.time()} | [{i}/{len(wallets)}] | {wallet_address} | Squid Router | {tx_hash.hex()}')
                    else:
                        print(
                            Fore.RED + f'{current_time.date()} {current_time.time()} | [{i}/{len(wallets)}] | {wallet_address} | Squid Router | {tx_hash.hex()} - Failed')

                    return tx_hash.hex()

                except ValueError as e:
                    if 'insufficient funds' in str(e):
                        logging.error(f'Insufficient funds for gas * price + value: {wallet_address}')
                        break
                    logging.error(f'Error occurred for wallet {wallet_address}: {e}')
                    logging.exception("Exception occurred", exc_info=True)
                    return None

            except KeyError as e:
                logging.error(f"KeyError: {e} in response data: {response_data}")
                continue

        except requests.RequestException as e:
            logging.error(f"Request exception: {e}")
            return None
        except ValueError as e:
            if 'insufficient funds' in str(e):
                logging.error(f'Insufficient funds for gas * price + value: {wallet_address}')
                break
            logging.error(f'Error occurred for wallet {wallet_address}: {e}')
            logging.exception("Exception occurred", exc_info=True)
            return None

# Пример использования функции для всех кошельков
gas_price_threshold_gwei = GAS_PRICE
for i, (wallet_address, private_key) in enumerate(zip(wallets, private_keys), start=1):
    try:
        squid_bridge(wallet_address, private_key, web3, i)
    except ValueError as e:
        if 'insufficient funds' in str(e):
            logging.error(f'Skipping wallet {wallet_address} due to insufficient funds.')
        else:
            raise e
    delay = random.randint(MIN_DELAY, MAX_DELAY)
    current_time = datetime.now()
    print(
        f'{current_time.date()} {current_time.time()} | [{i}/{len(wallets)}] | {wallet_address} | Wait {delay} seconds')
    print('')
    time.sleep(delay)
