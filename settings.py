# Delay - задержка между аккаунтами в секундах
MIN_DELAY = 10000
MAX_DELAY = 50000

# Контроль Gwei
GAS_PRICE = 50

# Сколько отправляем % от баланса
MIN_BALANCE = 0.85   # Например, 85%
MAX_BALANCE = 0.9   # Например, 90%

# RPC чейна отправления
RPC_URL = 'https://rpc.ankr.com/arbitrum'

# CHAIN ID чейна отправления
chainId_sent = 42161  # Укажи chain id, с которого будем отправлять бабки

# Random Chain получателя
RANDOM_RECIVE = False    # True / False

# Если используешь рандомного получателя - True (можешь выбрать используемые чейны)
# Если какой-то чейн не нужен, просто закомментируй его (#)
# Также закомментируй чейн отправителя в этом списке для корректной отправки
# Можешь сам добавлять любые чейны - смотреть тут - https://app.squidrouter.com/

chain_ids = {
    #42161: "ARB",
    10: "OP",
    534352: "SCROLL",
    42170: "ARB_NOVA",
    8453: "BASE",
    1: "ETH",
    1101: "ZKEVM",
    690: "REDSTONE",
    #324: "ZKSYNC"
}

# Если используешь конкретного получателя - False (можешь выбрать используемые чейны)
chain_recive = {
    534352: "SCROLL"   # Пример замены: 10: "OP"
}

#Какой токен отправляем:

from_token = '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'    # ETH
to_token = '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'    # ETH

slippage = 1.5 # Можешь выбрать сам, но по дефолту стоит как на сайте
