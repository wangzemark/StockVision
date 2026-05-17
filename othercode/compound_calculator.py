import matplotlib.pyplot as plt

def dca_calculator_with_inflation(annual_return_rate, annual_inflation_rate, freq, amount, years):
    """
    考虑通胀的定投复利计算器
    :param annual_return_rate: 年化收益率 (如 0.1)
    :param annual_inflation_rate: 年化通胀率 (如 0.03)
    :param freq: 定投频率 ('day', 'week', 'month', 'year')
    :param amount: 每期定投金额
    :param years: 定投持续年数
    """
    
    # 频率转换
    freq_map = {'day': 365, 'week': 52, 'month': 12, 'year': 1}
    n_periods_per_year = freq_map[freq]
    total_periods = int(years * n_periods_per_year)
    
    period_return_rate = annual_return_rate / n_periods_per_year
    # 计算每一期的通胀折现率
    period_inflation_rate = annual_inflation_rate / n_periods_per_year
    
    total_balance = 0      # 名义总金额（账面价值）
    total_principal = 0    # 累计投入本金
    
    history_balance = []
    history_principal = []
    history_real_value = [] # 实际购买力历史
    
    for i in range(1, total_periods + 1):
        total_principal += amount
        # 计算名义复利：期初投入，期末结算
        total_balance = (total_balance + amount) * (1 + period_return_rate)
        
        # 计算该时间点的实际购买力 (将当前名义总额折算回第0天的价值)
        # 购买力折现公式: 名义价值 / (1 + 每期通胀率)^当前期数
        real_value = total_balance / ((1 + period_inflation_rate) ** i)
        
        history_balance.append(total_balance)
        history_principal.append(total_principal)
        history_real_value.append(real_value)
    
    # 最终指标
    total_interest = total_balance - total_principal
    profit_rate = (total_interest / total_principal) * 100
    final_real_value = history_real_value[-1]
    
    # --- 输出结果 ---
    print(f"{'='*40}")
    print(f"定投复利计算结果 (持续 {years} 年, 考虑通胀)")
    print(f"{'='*40}")
    print(f"1. 累计投入本金:           {total_principal:,.2f}")
    print(f"2. 最终名义总金额(本+息):   {total_balance:,.2f}")
    print(f"3. 净利润总额:             {total_interest:,.2f}")
    print(f"4. 净利润率 (息/本):        {profit_rate:.2f}%")
    print(f"5. 实际购买力总金额:        {final_real_value:,.2f}")
    print(f"   (注：按{annual_return_rate*100}%年化收益率，{annual_inflation_rate*100}%通胀率折算至今日价值)")
    print(f"{'='*40}")
    
    # # --- 绘图 ---
    # plt.figure(figsize=(12, 7))
    # plt.plot(history_balance, label='Nominal Total (账面总额)', color='blue', linewidth=2)
    # plt.plot(history_principal, label='Total Principal (投入本金)', color='orange', linestyle='--')
    # plt.plot(history_real_value, label='Real Purchasing Power (实际购买力)', color='green', linewidth=2)
    
    # plt.title(f'DCA Investment: Nominal vs Real Value ({years} Years)')
    # plt.xlabel(f'Periods ({freq})')
    # plt.ylabel('Amount')
    # plt.legend()
    # plt.grid(True, alpha=0.3)
    # plt.show()

# --- 用户设定 ---
dca_calculator_with_inflation(
    annual_return_rate = 0.15,    
    annual_inflation_rate = 0.03, 
    freq = 'week',               
    amount = 100,              
    years = 1.5              
)