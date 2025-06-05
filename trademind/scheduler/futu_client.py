#!/usr/bin/env python3
"""
富途API客户端

基于富途OpenAPI实现的客户端，提供股票数据和交易功能。
文档: https://openapi.futunn.com/futu-api-doc/
"""

import logging
from typing import Dict, List, Optional, Any, Union
import futu as ft
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FutuClient:
    """富途API客户端"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化富途客户端
        
        Args:
            config: 配置字典，包含host, port, unlock_pwd等
        """
        self.host = config.get("host", "127.0.0.1")
        self.port = config.get("port", 11111)
        self.unlock_pwd = config.get("unlock_pwd")
        
        # 行情上下文
        self.quote_ctx = None
        # 交易上下文
        self.trade_ctx = None
        
        self.last_error = None
        
        # 初始化连接
        self._initialize_connections()
    
    def _initialize_connections(self):
        """初始化富途API连接"""
        try:
            # 初始化行情上下文
            self.quote_ctx = ft.OpenQuoteContext(host=self.host, port=self.port)
            logger.info(f"富途行情API连接成功: {self.host}:{self.port}")
            
            # 如果有解锁密码，初始化交易上下文
            if self.unlock_pwd:
                self.trade_ctx = ft.OpenSecTradeContext(
                    filter_trdmarket=ft.TrdMarket.US,  # 美股交易
                    host=self.host,
                    port=self.port,
                    security_firm=ft.SecurityFirm.FUTUSECURITIES
                )
                
                # 解锁交易
                ret, data = self.trade_ctx.unlock_trade(self.unlock_pwd)
                if ret == ft.RET_OK:
                    logger.info("富途交易API解锁成功")
                else:
                    logger.warning(f"富途交易API解锁失败: {data}")
                    self.trade_ctx = None
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"富途API连接失败: {e}")
    
    def get_watchlist(self) -> Dict[str, str]:
        """
        获取自选股列表
        
        Returns:
            Dict[str, str]: 股票代码到股票名称的映射
        """
        try:
            if not self.quote_ctx:
                raise Exception("行情API未连接")
            
            # 获取自选股分组
            ret, data = self.quote_ctx.get_user_security_group(ft.UserSecurityGroupType.ALL)
            if ret != ft.RET_OK:
                raise Exception(f"获取自选股分组失败: {data}")
            
            watchlist = {}
            
            # 遍历所有分组获取股票
            if not data.empty:
                for _, group in data.iterrows():
                    group_name = group.get('group_name', '')
                    
                    # 获取分组内的股票
                    ret, stocks = self.quote_ctx.get_user_security(group_name)
                    if ret == ft.RET_OK and not stocks.empty:
                        for _, stock in stocks.iterrows():
                            code = stock.get('code', '')
                            name = stock.get('name', code)
                            if code:  # 确保代码不为空
                                watchlist[code] = name
            
            return watchlist
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"获取自选股失败: {e}")
            return {}
    
    def get_stock_quote(self, stock_code: str) -> Dict[str, Any]:
        """
        获取股票实时报价
        
        Args:
            stock_code: 股票代码，如 'US.AAPL', 'HK.00700'
            
        Returns:
            Dict[str, Any]: 股票报价数据
        """
        try:
            if not self.quote_ctx:
                raise Exception("行情API未连接")
            
            # 订阅股票
            ret, err = self.quote_ctx.subscribe([stock_code], [ft.SubType.QUOTE])
            if ret != ft.RET_OK:
                logger.warning(f"订阅股票失败: {err}")
            
            # 获取实时报价
            ret, data = self.quote_ctx.get_stock_quote([stock_code])
            if ret != ft.RET_OK:
                raise Exception(f"获取报价失败: {data}")
            
            if data.empty:
                return {}
            
            # 转换为字典格式
            quote = data.iloc[0]
            result = {
                "股票代码": quote.get('code', stock_code),
                "股票名称": quote.get('stock_name', ''),
                "最新价": quote.get('last_price', 0),
                "开盘价": quote.get('open_price', 0),
                "昨收价": quote.get('prev_close_price', 0),
                "最高价": quote.get('high_price', 0),
                "最低价": quote.get('low_price', 0),
                "成交量": quote.get('volume', 0),
                "成交额": quote.get('turnover', 0),
                "涨跌额": quote.get('change_val', 0),
                "涨跌幅": f"{quote.get('change_rate', 0):.2f}%",
                "更新时间": quote.get('update_time', ''),
                "市场状态": quote.get('stock_status', ''),
            }
            
            return result
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"获取股票报价失败: {e}")
            return {}
    
    def get_stock_history(self, stock_code: str, period: str = "day", count: int = 30) -> List[Dict[str, Any]]:
        """
        获取股票历史K线数据
        
        Args:
            stock_code: 股票代码
            period: K线周期 (1min, 5min, 15min, 30min, 60min, day, week, month)
            count: 获取数据条数
            
        Returns:
            List[Dict[str, Any]]: 历史K线数据列表
        """
        try:
            if not self.quote_ctx:
                raise Exception("行情API未连接")
            
            # 转换周期参数
            ktype_map = {
                "1min": ft.KLType.K_1M,
                "5min": ft.KLType.K_5M,
                "15min": ft.KLType.K_15M,
                "30min": ft.KLType.K_30M,
                "60min": ft.KLType.K_60M,
                "day": ft.KLType.K_DAY,
                "week": ft.KLType.K_WEEK,
                "month": ft.KLType.K_MON
            }
            
            ktype = ktype_map.get(period, ft.KLType.K_DAY)
            
            # 计算开始日期
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=count * 2)).strftime('%Y-%m-%d')
            
            # 获取历史数据
            ret, data = self.quote_ctx.get_history_kline(
                code=stock_code,
                start=start_date,
                end=end_date,
                ktype=ktype,
                max_count=count
            )
            
            if ret != ft.RET_OK:
                raise Exception(f"获取历史数据失败: {data}")
            
            if data.empty:
                return []
            
            # 转换为字典列表
            result = []
            for _, row in data.iterrows():
                kline = {
                    "日期": row.get('time_key', ''),
                    "开盘价": row.get('open', 0),
                    "最高价": row.get('high', 0),
                    "最低价": row.get('low', 0),
                    "收盘价": row.get('close', 0),
                    "成交量": row.get('volume', 0),
                    "成交额": row.get('turnover', 0),
                    "涨跌额": row.get('change_val', 0),
                    "涨跌幅": f"{row.get('change_rate', 0):.2f}%",
                }
                result.append(kline)
            
            return result[-count:]  # 返回最近count条数据
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"获取股票历史数据失败: {e}")
            return []
    
    def search_stock(self, keyword: str, market: str = "ALL", limit: int = 10) -> List[Dict[str, Any]]:
        """
        搜索股票
        
        Args:
            keyword: 搜索关键词
            market: 市场类型 (US, HK, SH, SZ, ALL)
            limit: 返回结果数量限制
            
        Returns:
            List[Dict[str, Any]]: 搜索结果列表
        """
        try:
            if not self.quote_ctx:
                raise Exception("行情API未连接")
            
            # 转换市场参数
            market_map = {
                "US": ft.Market.US,
                "HK": ft.Market.HK,
                "SH": ft.Market.SH,
                "SZ": ft.Market.SZ,
                "ALL": None
            }
            
            markets = [market_map[market]] if market != "ALL" else [ft.Market.US, ft.Market.HK, ft.Market.SH, ft.Market.SZ]
            
            all_results = []
            
            for mkt in markets:
                if mkt is None:
                    continue
                    
                # 搜索股票
                ret, data = self.quote_ctx.get_stock_basicinfo(market=mkt, stock_type=ft.SecurityType.STOCK)
                if ret != ft.RET_OK:
                    continue
                
                # 过滤搜索结果
                filtered = data[
                    data['name'].str.contains(keyword, case=False, na=False) |
                    data['code'].str.contains(keyword, case=False, na=False)
                ]
                
                for _, row in filtered.head(limit).iterrows():
                    result = {
                        "股票代码": row.get('code', ''),
                        "股票名称": row.get('name', ''),
                        "市场": row.get('market', ''),
                        "股票类型": row.get('stock_type', ''),
                        "上市状态": row.get('list_status', ''),
                    }
                    all_results.append(result)
                    
                    if len(all_results) >= limit:
                        break
                
                if len(all_results) >= limit:
                    break
            
            return all_results[:limit]
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"搜索股票失败: {e}")
            return []
    
    def get_market_snapshot(self, market: str = "US") -> Dict[str, Any]:
        """
        获取市场快照
        
        Args:
            market: 市场类型 (US, HK, CN)
            
        Returns:
            Dict[str, Any]: 市场快照数据
        """
        try:
            if not self.quote_ctx:
                raise Exception("行情API未连接")
            
            # 根据市场获取主要指数
            index_codes = {
                "US": ["US.SPY", "US.QQQ", "US.DIA"],  # 标普500, 纳斯达克, 道琼斯
                "HK": ["HK.800000", "HK.800100"],      # 恒生指数, 恒生科技指数
                "CN": ["SH.000001", "SZ.399001"]       # 上证指数, 深证成指
            }
            
            codes = index_codes.get(market, index_codes["US"])
            
            # 获取指数报价
            ret, data = self.quote_ctx.get_stock_quote(codes)
            if ret != ft.RET_OK:
                raise Exception(f"获取市场数据失败: {data}")
            
            snapshot = {
                "市场": market,
                "更新时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "主要指数": []
            }
            
            for _, row in data.iterrows():
                index_info = {
                    "代码": row.get('code', ''),
                    "名称": row.get('stock_name', ''),
                    "最新价": row.get('last_price', 0),
                    "涨跌额": row.get('change_val', 0),
                    "涨跌幅": f"{row.get('change_rate', 0):.2f}%",
                }
                snapshot["主要指数"].append(index_info)
            
            return snapshot
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"获取市场快照失败: {e}")
            return {}
    
    def get_account_info(self, account_type: str = "SIMULATE") -> Dict[str, Any]:
        """
        获取账户信息
        
        Args:
            account_type: 账户类型 (REAL, SIMULATE)
            
        Returns:
            Dict[str, Any]: 账户信息
        """
        try:
            if not self.trade_ctx:
                raise Exception("交易API未连接或未解锁")
            
            # 获取账户列表
            ret, data = self.trade_ctx.get_acc_list()
            if ret != ft.RET_OK:
                raise Exception(f"获取账户列表失败: {data}")
            
            # 查找指定类型的账户
            target_acc = None
            for _, acc in data.iterrows():
                acc_type = acc.get('trd_env', '')
                if (account_type == "SIMULATE" and acc_type == ft.TrdEnv.SIMULATE) or \
                   (account_type == "REAL" and acc_type == ft.TrdEnv.REAL):
                    target_acc = acc
                    break
            
            if target_acc is None:
                raise Exception(f"未找到{account_type}类型账户")
            
            acc_id = target_acc['acc_id']
            
            # 获取账户资金
            ret, funds = self.trade_ctx.get_funds()
            if ret != ft.RET_OK:
                raise Exception(f"获取资金信息失败: {funds}")
            
            account_info = {
                "账户ID": acc_id,
                "账户类型": account_type,
                "总资产": funds.iloc[0].get('total_assets', 0) if not funds.empty else 0,
                "现金": funds.iloc[0].get('cash', 0) if not funds.empty else 0,
                "市值": funds.iloc[0].get('market_val', 0) if not funds.empty else 0,
                "可用资金": funds.iloc[0].get('avl_withdrawal_cash', 0) if not funds.empty else 0,
                "购买力": funds.iloc[0].get('power', 0) if not funds.empty else 0,
                "更新时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            return account_info
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"获取账户信息失败: {e}")
            return {}
    
    def get_positions(self, account_type: str = "SIMULATE") -> List[Dict[str, Any]]:
        """
        获取持仓信息
        
        Args:
            account_type: 账户类型 (REAL, SIMULATE)
            
        Returns:
            List[Dict[str, Any]]: 持仓信息列表
        """
        try:
            if not self.trade_ctx:
                raise Exception("交易API未连接或未解锁")
            
            # 获取持仓
            ret, data = self.trade_ctx.get_position_list()
            if ret != ft.RET_OK:
                raise Exception(f"获取持仓失败: {data}")
            
            if data.empty:
                return []
            
            positions = []
            for _, pos in data.iterrows():
                position_info = {
                    "股票代码": pos.get('code', ''),
                    "股票名称": pos.get('stock_name', ''),
                    "持仓数量": pos.get('qty', 0),
                    "可卖数量": pos.get('can_sell_qty', 0),
                    "成本价": pos.get('cost_price', 0),
                    "当前价": pos.get('nominal_price', 0),
                    "市值": pos.get('market_val', 0),
                    "盈亏": pos.get('pl_val', 0),
                    "盈亏比例": f"{pos.get('pl_ratio', 0):.2f}%",
                    "持仓方向": pos.get('position_side', ''),
                }
                positions.append(position_info)
            
            return positions
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"获取持仓信息失败: {e}")
            return []
    
    def close(self):
        """关闭连接"""
        try:
            if self.quote_ctx:
                self.quote_ctx.close()
                self.quote_ctx = None
            
            if self.trade_ctx:
                self.trade_ctx.close()
                self.trade_ctx = None
                
            logger.info("富途API连接已关闭")
            
        except Exception as e:
            logger.error(f"关闭富途API连接失败: {e}")
    
    def __del__(self):
        """析构函数，确保连接被关闭"""
        self.close() 