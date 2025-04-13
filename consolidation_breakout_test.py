import csv
from pathlib import Path
import pprint

REMAIN_OUTSIDE_OF_BAND_FOR_N_PERIODS = 4
MIN_CONSECUTIVE_EXTREMES = 3
MOVE_BY_N_AFTER_CONSECUTIVE_EXTREMES = 1.0 # Price difference for consolidated high/low identification

def reset_state():
    return {
        'price': float(0),
        'trade_placed': False,
        'trade_closed': False,
        'past_band_upper': False,
        'past_band_lower': False,
        'past_band_upper_count': 0,
        # 'past_band_lower_count': 0,
        'past_band_upper_for_n_periods': False,
        # 'past_band_lower_for_n_periods': False,
        'reached_consolidation_point_high': False,
        # 'reached_consolidation_point_low': False,
        'consecutive_highs_count': 0,
        # 'consecutive_lows_count': 0,
        'consolidation_price_high': float('inf')#,
        # 'consolidation_price_low': float('-inf'),
        'price_change': 0,
        'profit_price': None,
        'stoploss_price':None
    }

state = reset_state()

prev_state = state.copy()

with (Path('data') / 'input.csv').open() as input_file:
    csv_reader = csv.DictReader(input_file)
    for row in csv_reader:
        event_date = row['event_date']
        price = float(row['price'])
        band_upper = float(row['band_upper'])
        band_lower = float(row['band_lower'])
        print(f"event_date: {event_date}")
        print(f"price: {price}")
        print(f"band_upper: {band_upper}")
        print(f"band_lower: {band_lower}")

        state['price'] = price

        if not state['trade_placed']:
            state['past_band_upper'] = True if price > band_upper else False
            state['past_band_lower'] = True if price < band_lower else False

            if prev_state['past_band_upper'] and not state['past_band_upper']:
                state = reset_state()
            elif prev_state['past_band_lower'] and not state['past_band_lower']:
                state = reset_state()
            else:
                if state['past_band_upper']:
                    state['past_band_upper_count'] = prev_state['past_band_upper_count'] + 1
                    if state['past_band_upper_count'] >= REMAIN_OUTSIDE_OF_BAND_FOR_N_PERIODS:
                        state['past_band_upper_for_n_periods'] = True

                    state['price_change'] = price - prev_state['price']

                    if not state['reached_consolidation_point_high'] and
                       state['price_change'] <= MOVE_BY_N_AFTER_CONSECUTIVE_EXTREMES and
                       prev_state['price_change'] >= MOVE_BY_N_AFTER_CONSECUTIVE_EXTREMES:
                       
                       state['reached_consolidation_point_high'] = True
                       state['consolidation_price_high'] = prev_state['price']

                    if state['reached_consolidation_point_high'] and state['past_band_upper_for_n_periods'] and
                        price > state['consolidation_price_high']: 

                        state['trade_placed'] = True
                        
                        state['profit_price'] = state['consolidation_price_high'] + (state['consolidation_price_high'] - band_lower) * PROFIT_MULTIPLIER
                        state['stoploss_price'] = state['consolidation_price_high'] - (state['consolidation_price_high'] - band_lower) * STOPLOSS_MULTIPLIER 

                        # ib api call to place buy order -- this is the entry order
                        # ib api call to set sell profit and puke prices -- these are the out orders


                elif state['past_band_lower']: 
                    if not state['reached_consolidation_point_low'] and
                       state['price_change'] >= MOVE_BY_N_AFTER_CONSECUTIVE_EXTREMES and
                       prev_state['price_change'] <= MOVE_BY_N_AFTER_CONSECUTIVE_EXTREMES:
                       
                       state['reached_consolidation_point_low'] = True
                       state['consolidation_price_low'] = prev_state['price']

                    if state['reached_consolidation_point_low'] and state['past_band_lower_for_n_periods'] and
                        price > state['consolidation_price_low']: 

                        state['trade_placed'] = True
                        
                        state['profit_price'] = state['consolidation_price_low'] - (band_lower - state['consolidation_price_low']) * PROFIT_MULTIPLIER 
                        state['stoploss_price'] = state['consolidation_price_low'] + (band_upper - state['consolidation_price_low'] - ) * STOPLOSS_MULTIPLIER 

                        # ib api call to place sell order -- this is the entry order
                        # ib api call to set buy profit and puke prices -- these are the out orders


                    if not prev_state['reached_consolidation_point_high']:
                        if prev_state['consecutive_highs_count'] >= MIN_CONSECUTIVE_EXTREMES:
                            if price > prev_state['price']:
                                state['consecutive_highs_count'] = prev_state['consecutive_highs_count'] + 1
                            elif price < prev_state['price']:
                                if price >= prev_state['price'] - MOVE_BY_N_AFTER_CONSECUTIVE_EXTREMES:
                                    state['consecutive_highs_count'] = 0
                                else:
                                    state['reached_consolidation_point_high'] = True
                                    state['consolidation_price_high'] = prev_state['price']
                        elif prev_state['consecutive_highs_count'] < MIN_CONSECUTIVE_EXTREMES:
                            if price > prev_state['price']:
                                state['consecutive_highs_count'] = prev_state['consecutive_highs_count'] + 1
                            else:
                                state['consecutive_highs_count'] = 0

                    if state['past_band_upper_for_n_periods']:
                        if prev_state['reached_consolidation_point_high']:
                            if price > state['consolidation_price_high']:
                                state['trade_placed'] = True

                elif state['past_band_lower']:
                    pass

                else:
                    state = reset_state()
        else: # Code for if a trade is placed
            pass


        prev_state = state.copy()

        print(f"state: ")
        pprint.pprint(state)
        print("")
