import numpy as np
import pandas as pd

def run_price_action_strategy(df, min_rr):
    zones = []
    trades = []
    
    # 1. Identify Supply/Demand Zones
    for i in range(2, len(df)-1):
        body_prev = abs(df['Close'].iloc[i-1] - df['Open'].iloc[i-1])
        body_curr = abs(df['Close'].iloc[i] - df['Open'].iloc[i])
        
        # Demand Zone: Small candle followed by large green
        if body_curr > body_prev * 3 and df['Close'].iloc[i] > df['Open'].iloc[i]:
            zones.append({
                'type': 'Demand',
                'top': max(df['Open'].iloc[i-1], df['Close'].iloc[i-1]),
                'bottom': df['Low'].iloc[i-1],
                'time': df.index[i-1],
                'start_idx': i,
                'active': True
            })
            
        # Supply Zone: Small candle followed by large red
        elif body_curr > body_prev * 3 and df['Close'].iloc[i] < df['Open'].iloc[i]:
            zones.append({
                'type': 'Supply',
                'top': df['High'].iloc[i-1],
                'bottom': min(df['Open'].iloc[i-1], df['Close'].iloc[i-1]),
                'time': df.index[i-1],
                'start_idx': i,
                'active': True
            })

    # 2. Simulate Trade Execution based on Zones and Risk/Reward
    for z in zones:
        entry_price = z['top'] if z['type'] == 'Demand' else z['bottom']
        sl_price = z['bottom'] if z['type'] == 'Demand' else z['top']
        risk = abs(entry_price - sl_price)
        
        if risk == 0: continue # Skip if risk is zero to avoid division errors
        
        # Calculate Take Profit based on minimum RR
        tp_price = entry_price + (risk * min_rr) if z['type'] == 'Demand' else entry_price - (risk * min_rr)
        
        # Look forward in time for price to re-enter the zone
        for j in range(z['start_idx'] + 1, len(df)):
            curr_low = df['Low'].iloc[j]
            curr_high = df['High'].iloc[j]
            
            # LONG Entry Trigger
            if z['type'] == 'Demand' and curr_low <= entry_price and z['active']:
                z['active'] = False # Zone is mitigated
                outcome = "Pending"
                pnl = 0
                
                # Check for SL or TP hit
                for k in range(j, len(df)):
                    if df['Low'].iloc[k] <= sl_price:
                        outcome = "Loss"
                        pnl = -1 # Lost 1 Risk Unit
                        break
                    elif df['High'].iloc[k] >= tp_price:
                        outcome = "Win"
                        pnl = min_rr # Won 'min_rr' Risk Units
                        break
                        
                trades.append({
                    'entry_time': df.index[j], 
                    'type': 'Long', 
                    'entry': round(entry_price, 4), 
                    'sl': round(sl_price, 4), 
                    'tp': round(tp_price, 4), 
                    'outcome': outcome, 
                    'pnl': pnl
                })
                break # Move to next zone once a trade is taken
                
            # SHORT Entry Trigger
            elif z['type'] == 'Supply' and curr_high >= entry_price and z['active']:
                z['active'] = False # Zone is mitigated
                outcome = "Pending"
                pnl = 0
                
                # Check for SL or TP hit
                for k in range(j, len(df)):
                    if df['High'].iloc[k] >= sl_price:
                        outcome = "Loss"
                        pnl = -1
                        break
                    elif df['Low'].iloc[k] <= tp_price:
                        outcome = "Win"
                        pnl = min_rr
                        break
                        
                trades.append({
                    'entry_time': df.index[j], 
                    'type': 'Short', 
                    'entry': round(entry_price, 4), 
                    'sl': round(sl_price, 4), 
                    'tp': round(tp_price, 4), 
                    'outcome': outcome, 
                    'pnl': pnl
                })
                break

    return {"trades": trades, "zones": zones}
