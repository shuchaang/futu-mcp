import futu as ft
from trademind.scheduler.futu_client import FutuClient

# 初始化 FutuClient
client = FutuClient({'host': '127.0.0.1', 'port': 11111})

def test_normal():
    """测试正常筛选场景"""
    simple_filter = ft.SimpleFilter()
    simple_filter.filter_min = 2
    simple_filter.filter_max = 1000
    simple_filter.stock_field = ft.StockField.CUR_PRICE
    simple_filter.is_no_filter = False
    # simple_filter.sort = SortDir.ASCEND

    financial_filter = ft.FinancialFilter()
    financial_filter.filter_min = 0.5
    financial_filter.filter_max = 50
    financial_filter.stock_field = ft.StockField.CURRENT_RATIO
    financial_filter.is_no_filter = False
    financial_filter.sort = ft.SortDir.ASCEND
    financial_filter.quarter = ft.FinancialQuarter.ANNUAL

    custom_filter = ft.CustomIndicatorFilter()
    custom_filter.ktype = ft.KLType.K_DAY
    custom_filter.stock_field1 = ft.StockField.MA10
    custom_filter.stock_field2 = ft.StockField.MA60
    custom_filter.relative_position = ft.RelativePosition.MORE
    custom_filter.is_no_filter = False
    filter_list = [simple_filter, financial_filter, custom_filter] 
    
    result = client.get_stock_filter(
        market=ft.Market.HK,  # 使用 Market 枚举
        filter_list=filter_list,
        plate_code='HK.Motherboard',
        begin=0,
        num=10
    )
    assert isinstance(result, list), f"返回类型应为list，实际为{type(result)}: {result}"
    print("✅ 正常筛选通过，返回数量：", len(result))
    for stock in result:
        code = stock.get('code', stock.get('security', {}).get('code', ''))
        name = stock.get('name', '')
        print(f"{code} - {name}")

def test_invalid_filter_type():
    """测试非法 filter_list 类型"""
    # filter_list 不是 SimpleFilter
    filter_list = [{"stock_field": "MarketVal", "filter_min": 1, "is_no_filter": False}]
    result = client.get_stock_filter(market=ft.Market.HK, filter_list=filter_list)
    assert isinstance(result, dict) and "error" in result, "应返回错误信息"
    print("✅ filter_list 非法类型检测通过：", result["error"])

def test_invalid_stock_field():
    """测试非法 stock_field 类型"""
    # stock_field 不是 StockField 枚举
    simple_filter = ft.SimpleFilter()
    simple_filter.stock_field = "MarketVal"  # 非法的 stock_field 类型
    simple_filter.filter_min = 1
    simple_filter.is_no_filter = False
    filter_list = [simple_filter]
    result = client.get_stock_filter(market=ft.Market.HK, filter_list=filter_list)
    assert isinstance(result, dict) and "error" in result, "应返回错误信息"
    print("✅ stock_field 非法类型检测通过：", result["error"])

def test_empty_result():
    """测试空结果场景"""
    # 极端条件，返回空
    simple_filter = ft.SimpleFilter()
    simple_filter.stock_field = 'MARKET_VAL'
    simple_filter.filter_min = 1e13  # 1万亿
    simple_filter.is_no_filter = False
    filter_list = [simple_filter]
    result = client.get_stock_filter(market=ft.Market.HK, filter_list=filter_list)
    assert isinstance(result, list) and len(result) == 0, "应返回空列表"
    print("✅ 空结果检测通过")

def test_multiple_filters():
    """测试多个筛选条件"""
    # 测试市值和成交量
    filter1 = ft.SimpleFilter()
    filter1.stock_field = 'MARKET_VAL'  # 市值
    filter1.filter_min = 10000000000  # 100亿
    filter1.is_no_filter = False

    filter2 = ft.SimpleFilter()
    filter2.stock_field = 'VOLUME'  # 成交量
    filter2.filter_min = 1000000  # 100万股
    filter2.is_no_filter = False

    filter_list = [filter1, filter2]
    result = client.get_stock_filter(market=ft.Market.HK, filter_list=filter_list, num=5)
    assert isinstance(result, list), "应返回列表"
    print("✅ 多条件筛选通过，返回数量：", len(result))

if __name__ == "__main__":
    test_normal()
    test_invalid_filter_type()
    test_invalid_stock_field()
    test_empty_result()
    test_multiple_filters() 