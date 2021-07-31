import time
import pyupbit
import datetime

# upbit 접속 정보
access = "xx"
secret = "yy"

# 변동성 돌파 전략 K 값
k = 0.5 

# 거래할 코인 리스트
target_tickers = ["KRW-BTC","KRW-ETH"]

# 최소 거래 금액
minimum_krw = 5000

# 수수료(0.05 %) 제외한 비율
except_order_ratio = 0.9995


# 변동성 돌파 전략으로 매수 목표가 조회
def get_target_price(ticker, k):
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

# 시작 시간 조회
def get_start_time(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

# 잔고 조회
def get_balance(ticker):
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

# 현재가 조회
def get_current_price(ticker):
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]


# 해당 코인이 오늘 매수한 코인인지 판단(최소 거래금액 이상으로 보유한지 여부)
def is_today_buy(ticker):
    have_ticker_current_krw = get_current_price(ticker) * get_balance(ticker)   # 가지고 있는 코인 수 * 현재가 로 매도 시 금액 계산
    
    return True if(have_ticker_current_krw > minimum_krw) else False

# 매수 금액 계산
def buy_order_price(ticker, current_total_krw):
    # target 코인들 대상으로 오늘 매매한거(5000원 이상 보유한) 코인을 제외한 코인들의 수로 엔빵
    cnt = 0
    for ticker in target_tickers :
        if(not is_today_buy(ticker)) :      # 오늘 산 코인이 아니라면, 금액 엔빵 대상
            cnt = cnt + 1
    
    return (current_total_krw/cnt)

# 매수
def buy_market_order(ticker):
    target_price = get_target_price(ticker, k)
    current_price = get_current_price(ticker)
    current_total_krw = get_balance("KRW")            # 현재 보유 현금

    # 매수 조건에 해당하는 경우
    # 목표가 < 현재가 이고, 매수 가능한 조건(잔고 5000원 이상)
    # 매수 금액은 대상 코인 리스트 중 오늘 구매한 코인 대상을 제외한 금액
    if (target_price < current_price and current_total_krw > minimum_krw and not is_today_buy(ticker)):
        # 매수 주문
        upbit.buy_market_order(ticker, buy_order_price(ticker, current_total_krw) * except_order_ratio)
#         print("------------------------------------")
#         print("    ticker")
#         print(ticker)
#         print("    current_total_krw")
#         print(current_total_krw)
#         print("    buy_order_price")
#         print(buy_order_price(ticker, current_total_krw))
#         print("    buy_order_price *")
#         print(buy_order_price(ticker, current_total_krw)*len(target_tickers))
#         print("------------------------------------")
      

# 매도
def sell_market_order(ticker):
    current_krw = get_current_price(ticker) * get_balance(ticker)   # 가지고 있는 코인 수 * 현재가 로 매도 시 금액 계산
    # 매도 가능한 조건(현재 가진 코인의 가치가 5000원 이상)
    if (current_krw > minimum_krw):
        # 매도 주문
        upbit.sell_market_order(ticker, get_balance(ticker) * except_order_ratio)
#         print(current_krw)

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")


# 자동매매 시작
while True:
    for ticker in target_tickers : 
        try:
            now = datetime.datetime.now()
            start_time = get_start_time(ticker)
            end_time = start_time + datetime.timedelta(days=1)
    
            # 시작 ~ 마감-10초
            if start_time < now < end_time - datetime.timedelta(seconds=10):
                buy_market_order(ticker)
                    
            # 해당 시간이 아닌 경우. 매도
            else:
                # 매도 가능한 조건(현재 가진 코인의 양이 5000원 이상)
                sell_market_order(ticker)
            time.sleep(1)
            
        except Exception as e:
            print(e)
            time.sleep(1)