import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq

# --- Black-Scholes ---
def black_scholes(S, K, T, r, sigma, option_type='call'):
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2)*T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    if option_type == 'call':
        return S * norm.cdf(d1) - K * np.exp(-r*T) * norm.cdf(d2)
    elif option_type == 'put':
        return K * np.exp(-r*T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    else:
        raise ValueError("option_type must be 'call' or 'put'")

# --- Black-76 (Futures) ---
def black_76(F, K, T, r, sigma, option_type='call'):
    d1 = (np.log(F / K) + 0.5 * sigma**2 * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    df = np.exp(-r * T)
    
    if option_type == 'call':
        return df * (F * norm.cdf(d1) - K * norm.cdf(d2))
    elif option_type == 'put':
        return df * (K * norm.cdf(-d2) - F * norm.cdf(-d1))
    else:
        raise ValueError("option_type must be 'call' or 'put'")

# --- Unified Pricer ---
def price_option(model='spot', S_or_F=None, K=None, T=None, r=None, sigma=None, option_type='call'):
    if model == 'spot':
        return black_scholes(S_or_F, K, T, r, sigma, option_type)
    elif model == 'futures':
        return black_76(S_or_F, K, T, r, sigma, option_type)
    else:
        raise ValueError("model must be 'spot' or 'futures'")

# --- Greeks ---
def calculate_greeks_bs(S, K, T, r, sigma, option_type='call'):
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == 'call':
        delta = norm.cdf(d1)
        theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) 
                 - r * K * np.exp(-r * T) * norm.cdf(d2)) / 365
        rho = K * T * np.exp(-r * T) * norm.cdf(d2) / 100
    elif option_type == 'put':
        delta = norm.cdf(d1) - 1
        theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) 
                 + r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365
        rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100
    else:
        raise ValueError("option_type must be 'call' or 'put'")
    
    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    vega = S * norm.pdf(d1) * np.sqrt(T) / 100

    return {
        'Delta': round(delta, 4),
        'Gamma': round(gamma, 4),
        'Vega': round(vega, 4),
        'Theta': round(theta, 4),
        'Rho': round(rho, 4)
    }

def calculate_greeks_black76(F, K, T, r, sigma, option_type='call'):
    d1 = (np.log(F / K) + 0.5 * sigma**2 * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    df = np.exp(-r * T)

    gamma = norm.pdf(d1) / (F * sigma * np.sqrt(T))
    vega = F * norm.pdf(d1) * np.sqrt(T) * df / 100

    if option_type == 'call':
        delta = df * norm.cdf(d1)
        rho = T * K * df * norm.cdf(d2) / 100
        theta = (-F * norm.pdf(d1) * sigma * df / (2 * np.sqrt(T)) 
                 - r * F * norm.cdf(d1) * df) / 365
    elif option_type == 'put':
        delta = -df * norm.cdf(-d1)
        rho = -T * K * df * norm.cdf(-d2) / 100
        theta = (-F * norm.pdf(d1) * sigma * df / (2 * np.sqrt(T)) 
                 + r * F * norm.cdf(-d1) * df) / 365
    else:
        raise ValueError("option_type must be 'call' or 'put'")

    return {
        'Delta': round(delta, 4),
        'Gamma': round(gamma, 4),
        'Vega': round(vega, 4),
        'Theta': round(theta, 4),
        'Rho': round(rho, 4)
    }

def calculate_greeks(model='spot', S_or_F=None, K=None, T=None, r=None, sigma=None, option_type='call'):
    if model == 'spot':
        return calculate_greeks_bs(S_or_F, K, T, r, sigma, option_type)
    elif model == 'futures':
        return calculate_greeks_black76(S_or_F, K, T, r, sigma, option_type)
    else:
        raise ValueError("model must be 'spot' or 'futures'")

# --- Implied Volatility ---
def implied_volatility(option_market_price, S, K, T, r, option_type='call'):
    def objective_function(sigma):
        return black_scholes(S, K, T, r, sigma, option_type) - option_market_price

    try:
        test_low = black_scholes(S, K, T, r, 0.0001, option_type)
        test_high = black_scholes(S, K, T, r, 3.0, option_type)
        if not (test_low <= option_market_price <= test_high):
            return None
        implied_vol = brentq(objective_function, 0.0001, 3.0)
        return round(implied_vol, 4)
    except ValueError:
        return None

def implied_volatility_black76(option_market_price, F, K, T, r, option_type='call'):
    def objective_function(sigma):
        return black_76(F, K, T, r, sigma, option_type) - option_market_price

    try:
        test_low = black_76(F, K, T, r, 0.0001, option_type)
        test_high = black_76(F, K, T, r, 3.0, option_type)
        if not (test_low <= option_market_price <= test_high):
            return None
        implied_vol = brentq(objective_function, 0.0001, 3.0)
        return round(implied_vol, 4)
    except ValueError:
        return None

def get_implied_volatility(model='spot', market_price=None, S_or_F=None, K=None, T=None, r=None, option_type='call'):
    if model == 'spot':
        return implied_volatility(market_price, S_or_F, K, T, r, option_type)
    elif model == 'futures':
        return implied_volatility_black76(market_price, S_or_F, K, T, r, option_type)
    else:
        raise ValueError("model must be 'spot' or 'futures'")
