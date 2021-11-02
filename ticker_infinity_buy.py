import time
import pyupbit
import datetime
import telegram
import pandas as pd
import numpy as np

access = "JjKKScVhqHgw13kEdXkJOKkJw87fct8S48wAQgCY"
secret = "ExiLxFFWYwHdsi7mKGS9Fxm9WNI9kfNxF08VuRiC"

TOKEN = '2020050827:AAHKyThn-rkBCgbLaPc_O87OfEDZtwTu7ZY'
ID = '1796318367'
bot = telegram.Bot(TOKEN)

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute5", count=1)
    start_time = df.index[0]
    return start_time

def get_ma10(ticker):
    """10개봉 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=10)
    ma10 = df['close'].rolling(10).mean().iloc[-1]
    return ma10

def get_balance(ticker):
    """잔고 조회"""
    balances = pyupbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

def check_profit(ticker,price,total):
    buy_value = price * total
    current_price = get_current_price(ticker)
    current_value = current_price * total
    profit = round(((current_value/buy_value)-1)*100,2)
    return profit

def get_RSI(ticker, period, column='close'):

    df = pyupbit.get_ohlcv(ticker, interval="minute3", count=200)

    delta = df[column].diff(1)
    delta = delta.dropna()
    up = delta.copy()
    down = delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    df['up'] = up
    df['down'] = down
    df=df[df['up'].notnull()]
    #AVG_Gain = avg(df, period, column='up')
    #AVG_Loss = abs(avg(df, period, column='down'))
    df['AU'] = 0
    df['AD'] = 0
    df=df[df['AU'].notnull()]
    #sma(Simple Moving Average:단순이동평균)
    #df['AU'] = df['up'].rolling(14).mean()
    #df['AD'] = np.abs(df['down'].rolling(14).mean())

    #ewma(Exponential Moving Average)
    df['AU'] = up.ewm(com=period -1 , min_periods=period).mean()
    df['AD'] = np.abs(down.ewm(com=period -1, min_periods=period).mean())

    df['RS'] = df['AU']/df['AD']
    df['RSI'] = 100.0 - (100.0 / (1.0 + df['RS']))
    return df['RSI'][-1]

def get_volatility(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    df['volatility'] = (df['close']/df['open']-1)*100
    volatility = df.iloc[-1]['volatility']
    return volatility

def get_top5(rq):
    tickers = pyupbit.get_tickers(fiat="KRW")
    dfs = []
    for i in range(len(tickers)):
        volatility = round(get_volatility(tickers[i]),2)
        dfs.append(volatility)
        time.sleep(0.06)

    volatility = pd.DataFrame({"volatility": dfs})
    ticker = pd.DataFrame({"ticker": pyupbit.get_tickers(fiat="KRW")})
    sum = [ticker, volatility]
    all_volatility = pd.concat(sum, axis =1)
    final=all_volatility.sort_values(by = "volatility", ascending=False)
    if rq == 0:
        #Dataframe을 list로 변환
        #result = final.iloc[:5]
        result = final.iloc[0]['ticker'].values.tolist()
    elif rq ==1:
        #상위 상승률 top5 ticker명만 뽑기
        result = final.iloc[:5]['ticker'].values.tolist()
    else:
        #상위 상승률 top5 상승률만 뽑기
        result2 = final.iloc[:5]['volatility'].values.tolist()
    return result

# 로그인
#upbit = pyupbit.Upbit(access, secret)
bot.sendMessage(ID, '========start here========')
#trade_ticker = 'STORJ'
#ticker = 'KRW-STORJ'
#my_money = 1000000 #krw = get_balance("KRW")
first_buy = False
check_add_buy = False
check_inform = False
sell_all = False
possess_total = 0
n = 0
success = 0
'''
balance_df = pd.DataFrame(upbit.get_balances())
result = balance_df.loc[balance_df['currency'] == trade_ticker]
print('보유수량= ',float(result['balance']))
print('평단가= ',float(result['avg_buy_price']))
'''

while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-BTC")
        end_time = start_time + datetime.timedelta(minutes=5)

        if start_time < now < end_time - datetime.timedelta(seconds=7):
            check_inform = False
            check_add_buy = False
            first_money = 50000
            buy_money = 50000
            if n == 0 and first_buy == False:
                print('첫 매수 시작')
                result_get = get_top5(1)
                ticker = result_get[0]
                trade_ticker = ticker.replace('KRW-','')
                current_price = get_current_price(ticker)
                buy_ticker = trade_ticker
                buy_price =  current_price 
                first_buy_total =(first_money*0.9995)/buy_price
                bot.sendMessage(ID, str(buy_ticker) + '\n'
                                + "첫 매수가:" + str(buy_price) + '\n'
                                + "첫 매수량:" + str(first_buy_total) + '\n'
                                + "test...ing")
                first_buy = True
                avg_price = buy_price
                possess_total = first_buy_total
                possess_money = first_money + n*buy_money
                print('0회차' + '\n'
                      + "투자금: " + str(possess_money) + '\n'
                      + "첫 매수량: " + str(possess_total) + '\n')
            else:
                sell_all = False
                current_profit = check_profit(ticker,avg_price,possess_total)
                print("수익률: ",current_profit)
                if n < 100:
                    k = 2.5
                else:
                    k = 1
                if current_profit >=k and sell_all == False:
                    print('3%이상 매도 시작')
                    sell_price = get_current_price(ticker)
                    my_money = sell_price*(possess_total*0.9995)
                    success += 1
                    bot.sendMessage(ID, "==SELL_success==" + '\n'
                                    + str(success) + "번째 성공" + '\n'
                                    + "투자금액: " + str(possess_money) + '\n'
                                    + "매도가격: " + str(sell_price) + '\n'
                                    + "매도금액: " + str(my_money) + '\n'
                                    + "수익률: " + str(current_profit)+ '\n'
                                    + "test...ing")
                    n=0
                    first_buy = False
                    sell_all = True
            time.sleep(1)
        else:
            current_price = get_current_price(ticker)
            current_rsi = get_RSI(ticker,10)
            if current_price < avg_price and check_add_buy == False and current_rsi < 50:
                print('매수 하러 옴')
                add_buy_price =  current_price 
                add_buy_total =(buy_money*0.9995)/add_buy_price
                bot.sendMessage(ID, "==add_BUY==" + '\n'
                                + "add_buy price:" + str(add_buy_price) + '\n'
                                + "add_buy total:" + str(add_buy_total) + '\n'
                                + "test...ing")
                check_add_buy = True
                n += 1
                #평단가 계산
                print("평단 계산 중")
                possess_total += add_buy_total
                possess_money = first_money + n*buy_money
                avg_price = possess_money/possess_total
            elif current_price >= avg_price and check_add_buy == False:
                print('평단보다 비쌈')
                check_add_buy = True
                possess_money = first_money + n*buy_money

            if check_inform == False:
                print('현 상황 인폼 중')
                bot.sendMessage(ID, "==possession==" + '\n'
                                    + "회차: " + str(n) + '\n'
                                    + "투자금액: " + str(possess_money) + '\n'
                                    + "보유량: " + str(possess_total) + '\n'
                                    + "평단가: " + str(avg_price) + '\n'
                                    + "test...ing")
                check_inform = True
        time.sleep(1)
    except Exception as e:
        print(e)
        bot.sendMessage(ID, str(e))
        time.sleep(1)
