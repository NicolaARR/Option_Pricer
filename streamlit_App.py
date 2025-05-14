import streamlit as st
import datetime
import pandas as pd
from pricing import price_option, calculate_greeks, get_implied_volatility

st.set_page_config(page_title="Option Pricing Tool", layout="centered")
st.image("Arrow_Logo.jpg", width=200)
st.title("📊 Option Pricing & Risk Calculator")

st.markdown("This is the prototype of the option value calculator for stocks and futures. \
Options on stocks are calculated with the Black-Scholes model, while options on futures are calculated using the Black-76 model. \
For questions, inputs and comments, please contact: nmarfurt@arrowresources.com.")

# --- Session state for storing positions ---
if "positions" not in st.session_state:
    st.session_state.positions = []

st.markdown("---")
st.header("Option Inputs")

col1, col2 = st.columns(2)

with col1:
    instrument = st.selectbox("Underlying Instrument Type", ["stocks", "futures"])
    option_type = st.selectbox("Option Type", ["call", "put"])
    S_or_F = st.number_input("Current Price (Stock or Future)", min_value=0.0, value=100.0)
    K = st.number_input("Strike Price", min_value=0.0, value=100.0)
    book = st.selectbox("Assign to Book", ["Book 1", "Book 2", "Book 3", "Book 4", "Book 5", "Company Book"])

with col2:
    product_code = st.text_input("Product Code (e.g. GAS-MAR25)")
    r = st.number_input("Risk-Free Rate", min_value=0.0, value=0.03, format="%0.4f")
    entry_price = st.number_input("Entry Price (Premium Paid)", min_value=0.0, value=10.0)
    entry_date = st.date_input("Entry Date", value=datetime.date.today())
    expiry_date = st.date_input("Expiry Date", value=datetime.date.today() + datetime.timedelta(days=30))

st.markdown("---")
st.header("Market Data")

market_price = st.number_input("Current Market Price of Option", min_value=0.0, value=0.0)
use_iv = market_price > 0
sigma = None

if not use_iv:
    sigma = st.number_input("Volatility (if no market price)", min_value=0.0, value=0.2, format="%0.4f")
else:
    st.info("Implied Volatility will be calculated from the market price.")

st.markdown("---")
if st.button("Calculate"):
    today = datetime.date.today()
    T = (expiry_date - today).days / 365

    if T <= 0:
        st.error("Expiry must be in the future.")
    else:
        st.markdown("---")
        st.header("📈 Results")

        model_type = "spot" if instrument == "stocks" else "futures"

        if use_iv:
            iv = get_implied_volatility(model=model_type, market_price=market_price, S_or_F=S_or_F, K=K, T=T, r=r, option_type=option_type)
            if iv:
                sigma = iv
                st.metric("Implied Volatility", f"{iv * 100:.2f}%")
            else:
                st.warning("Implied Volatility could not be calculated. Using default vol = 0.2")
                sigma = 0.2
        else:
            st.metric("Input Volatility", f"{sigma * 100:.2f}%")

        model_price = price_option(model=model_type, S_or_F=S_or_F, K=K, T=T, r=r, sigma=sigma, option_type=option_type)
        pnl = model_price - entry_price

        st.metric("Model Price", f"${model_price:.2f}")
        st.metric("Unrealized PnL", f"${pnl:.2f}")

        st.subheader("Greeks")
        greeks = calculate_greeks(model=model_type, S_or_F=S_or_F, K=K, T=T, r=r, sigma=sigma, option_type=option_type)
        for g, v in greeks.items():
            st.write(f"{g}: {v}")

        # Store the position
        status = "Open" if expiry_date > today else "Closed"
        position = {
            "Book": book,
            "Product Code": product_code,
            "Instrument": instrument,
            "Type": option_type,
            "Strike": K,
            "Entry Date": entry_date,
            "Expiry Date": expiry_date,
            "Entry Price": entry_price,
            "Model Price": round(model_price, 2),
            "PnL": round(pnl, 2),
            "Status": status
        }
        position.update(greeks)
        st.session_state.positions.append(position)

# --- Display stored positions ---
st.markdown("---")
st.subheader("📋 Stored Option Positions")

if st.session_state.positions:
    df = pd.DataFrame(st.session_state.positions)

    # Filters
    selected_book = st.selectbox("Filter by Book", ["All"] + sorted(df["Book"].unique()))
    selected_status = st.selectbox("Filter by Status", ["All"] + sorted(df["Status"].unique()))

    if selected_book != "All":
        df = df[df["Book"] == selected_book]
    if selected_status != "All":
        df = df[df["Status"] == selected_status]

    st.dataframe(df)

    # Summary stats
    st.markdown("---")
    st.subheader("📊 Summary Statistics")
    st.write("Total Positions:", len(df))
    st.write("Total PnL:", f"${df['PnL'].sum():.2f}")
    st.write("Average Delta:", f"{df['Delta'].mean():.4f}")

    # Export button
    st.download_button("📥 Download to Excel", df.to_csv(index=False), file_name="option_positions.csv", mime="text/csv")

    # Clear all button
    if st.button("❌ Clear All Positions"):
        st.session_state.positions = []
        st.rerun()
else:
    st.info("No positions saved yet.")

# --- Excel Sheet Copier ---
st.markdown("---")
st.subheader("📁 Copy Sheet from One Excel File to Another")

source_file = st.file_uploader("Upload Source Excel File", type=["xlsx"])
target_file = st.file_uploader("Upload Target Excel File", type=["xlsx"])
source_sheet = st.text_input("Source Sheet Name")
target_sheet = st.text_input("Target Sheet Name")

if st.button("Copy Sheet"):
    if source_file and target_file and source_sheet and target_sheet:
        try:
            # Load source sheet as DataFrame
            source_df = pd.read_excel(source_file, sheet_name=source_sheet)

            # Load target workbook
            wb = openpyxl.load_workbook(target_file)

            # If sheet exists, delete it first
            if target_sheet in wb.sheetnames:
                del wb[target_sheet]

            # Add new sheet with copied content
            ws = wb.create_sheet(title=target_sheet)

            for r_idx, row in enumerate(source_df.itertuples(index=False), 1):
                for c_idx, value in enumerate(row, 1):
                    ws.cell(row=r_idx, column=c_idx).value = value

            # Save modified file to buffer
            output = BytesIO()
            wb.save(output)
            st.success("✅ Sheet copied successfully!")

            # Download button
            st.download_button("📥 Download Modified File", data=output.getvalue(), file_name="modified_target.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception as e:
            st.error(f"❌ Error: {e}")
    else:
        st.warning("Please upload both files and enter both sheet names.")


