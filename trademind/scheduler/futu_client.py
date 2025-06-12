#!/usr/bin/env python3
"""
富途API客户端

基于富途OpenAPI实现的客户端，提供股票数据和交易功能。
文档: https://openapi.futunn.com/futu-api-doc/
"""

import logging
from typing import Dict, List, Optional, Any, Union, Callable
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
        self._subscriptions = {}  # 订阅管理
        self._callbacks = {}      # 回调函数管理
        
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
                # 支持多市场交易
                self.trade_ctx = {
                    'US': ft.OpenSecTradeContext(
                        filter_trdmarket=ft.TrdMarket.US,
                        host=self.host,
                        port=self.port,
                        security_firm=ft.SecurityFirm.FUTUSECURITIES
                    ),
                    'HK': ft.OpenSecTradeContext(
                        filter_trdmarket=ft.TrdMarket.HK,
                        host=self.host,
                        port=self.port,
                        security_firm=ft.SecurityFirm.FUTUSECURITIES
                    ),
                    'CN': ft.OpenSecTradeContext(
                        filter_trdmarket=ft.TrdMarket.CN,
                        host=self.host,
                        port=self.port,
                        security_firm=ft.SecurityFirm.FUTUSECURITIES
                    )
                }
                
                # 解锁所有交易上下文
                for market, ctx in self.trade_ctx.items():
                    try:
                        ret, data = ctx.unlock_trade(self.unlock_pwd)
                        if ret == ft.RET_OK:
                            logger.info(f"富途{market}交易API解锁成功")
                        else:
                            logger.warning(f"富途{market}交易API解锁失败: {data}")
                    except Exception as e:
                        logger.error(f"富途{market}交易API解锁异常: {e}")
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"富途API连接失败: {e}")
    

    def get_user_security(self, group_name: str) -> List[Dict[str, Any]]:
        """
        获取指定分组的自选股列表
        
        Args:
            group_name: 分组名称，如 'All', 'US', 'HK', 'CN', 'Starred' 等
            
        Returns:
            List[Dict[str, Any]]: 自选股列表
        """
        try:
            if not self.quote_ctx:
                raise Exception("行情API未连接")
            
            # 获取指定分组的自选股
            ret, data = self.quote_ctx.get_user_security(group_name)
            if ret != ft.RET_OK:
                raise Exception(f"获取自选股分组 '{group_name}' 失败: {data}")
            
            if data.empty:
                return []
            
            securities = []
            for _, stock in data.iterrows():
                # 解析市场代码
                code = stock.get('code', '')
                market = 'Unknown'
                if code.startswith('US.'):
                    market = 'US'
                elif code.startswith('HK.'):
                    market = 'HK'
                elif code.startswith('SH.'):
                    market = 'SH'
                elif code.startswith('SZ.'):
                    market = 'SZ'
                
                # 根据富途API返回的字段构建股票信息
                security_info = {
                    "股票代码": code,
                    "股票名称": stock.get('name', ''),
                    "市场": market,
                    "每手股数": stock.get('lot_size', 0),
                    "股票类型": self._convert_security_type(stock.get('stock_type', '')),
                    "上市时间": stock.get('listing_date', ''),
                    "股票ID": stock.get('stock_id', ''),
                    "是否退市": stock.get('delisting', False),
                    "是否主连合约": stock.get('main_contract', False),
                }
                
                # 如果有期权相关字段，添加期权信息
                if stock.get('option_type'):
                    security_info.update({
                        "期权类型": stock.get('option_type', ''),
                        "行权日": stock.get('strike_time', ''),
                        "行权价": stock.get('strike_price', 0),
                        "是否停牌": stock.get('suspension', False),
                    })
                
                # 如果有窝轮信息，添加窝轮字段
                if stock.get('stock_child_type'):
                    security_info.update({
                        "窝轮子类型": stock.get('stock_child_type', ''),
                        "窝轮标的": stock.get('stock_owner', ''),
                    })
                
                # 如果有最后交易时间，添加该字段
                if stock.get('last_trade_time'):
                    security_info["最后交易时间"] = stock.get('last_trade_time', '')
                
                securities.append(security_info)
            
            return securities
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"获取自选股分组失败: {e}")
            return []
    
    def _convert_security_type(self, sec_type: Any) -> str:
        """
        转换证券类型为可读字符串
        
        Args:
            sec_type: 富途API返回的证券类型
            
        Returns:
            str: 可读的证券类型字符串
        """
        try:
            # 处理None或空值
            if sec_type is None or sec_type == '':
                return 'UNKNOWN'
                
            # 定义类型映射
            type_map = {
                1: 'STOCK',      # 股票
                2: 'OPTION',     # 期权
                3: 'FUTURE',     # 期货
                4: 'INDEX',      # 指数
                5: 'WARRANT',    # 窝轮
                6: 'BOND',       # 债券
                7: 'ETF',        # ETF
                8: 'SPOT',       # 外汇现货
                
                'STOCK': 'STOCK',
                'OPTION': 'OPTION',
                'FUTURE': 'FUTURE',
                'INDEX': 'INDEX',
                'WARRANT': 'WARRANT',
                'BOND': 'BOND',
                'ETF': 'ETF',
                'SPOT': 'SPOT'
            }
            
            # 如果是枚举类型，尝试获取name属性
            if hasattr(sec_type, 'name'):
                enum_name = sec_type.name
                return type_map.get(enum_name, 'UNKNOWN')
            
            # 如果是数字或者字符串，使用映射转换
            if sec_type in type_map:
                return type_map[sec_type]
            
            # 如果是字符串，尝试转换为大写
            if isinstance(sec_type, str):
                upper_type = sec_type.upper()
                return type_map.get(upper_type, 'UNKNOWN')
            
            # 其他情况返回UNKNOWN
            return 'UNKNOWN'
            
        except Exception as e:
            logger.error(f"证券类型转换失败: {e}, 原始类型: {sec_type}")
            return 'UNKNOWN'
    
    def get_user_security_group(self, group_type: str = "ALL") -> List[Dict[str, Any]]:
        """
        获取自选股分组列表
        
        Args:
            group_type: 分组类型筛选 (ALL, SYSTEM, CUSTOM)
            
        Returns:
            List[Dict[str, Any]]: 自选股分组列表
        """
        try:
            if not self.quote_ctx:
                raise Exception("行情API未连接")
            
            # 转换分组类型参数
            group_type_map = {
                "ALL": ft.UserSecurityGroupType.ALL,
                "SYSTEM": ft.UserSecurityGroupType.SYSTEM,
                "CUSTOM": ft.UserSecurityGroupType.CUSTOM
            }
            
            ft_group_type = group_type_map.get(group_type, ft.UserSecurityGroupType.ALL)
            
            # 获取自选股分组列表
            ret, data = self.quote_ctx.get_user_security_group(group_type=ft_group_type)
            if ret != ft.RET_OK:
                raise Exception(f"获取自选股分组列表失败: {data}")
            
            if data.empty:
                return []
            
            groups = []
            for _, group in data.iterrows():
                group_info = {
                    "分组名称": group.get('group_name', ''),
                    "分组类型": self._convert_group_type(group.get('group_type', '')),
                }
                groups.append(group_info)
            
            return groups
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"获取自选股分组列表失败: {e}")
            return []
    
    def _convert_group_type(self, group_type: Any) -> str:
        """
        转换分组类型为可读字符串
        
        Args:
            group_type: 富途API返回的分组类型
            
        Returns:
            str: 可读的分组类型字符串
        """
        type_map = {
            ft.UserSecurityGroupType.SYSTEM: 'SYSTEM',
            ft.UserSecurityGroupType.CUSTOM: 'CUSTOM',
            ft.UserSecurityGroupType.ALL: 'ALL',
        }
        
        # 如果是枚举类型，转换为字符串
        if hasattr(group_type, 'name'):
            return group_type.name
        
        # 如果是数字，根据映射转换
        for enum_type, type_str in type_map.items():
            if group_type == enum_type:
                return type_str
        
        # 如果已经是字符串，直接返回
        return str(group_type) if group_type else 'UNKNOWN'

    def get_positions(self, account_type: str = "REAL") -> List[Dict[str, Any]]:
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
            
            # 转换账户类型
            trd_env = ft.TrdEnv.REAL if account_type == "REAL" else ft.TrdEnv.SIMULATE
            
            # 遍历所有市场的交易上下文获取持仓
            all_positions = []
            for market, ctx in self.trade_ctx.items():
                try:
                    # 获取账户列表
                    ret, data = ctx.get_acc_list()
                    if ret != ft.RET_OK:
                        logger.warning(f"{market}市场获取账户列表失败: {data}")
                        continue
                    
                    # 查找指定类型的账户
                    target_acc = None
                    for _, acc in data.iterrows():
                        if acc.get('trd_env') == trd_env:
                            target_acc = acc
                            break
                    
                    if target_acc is None:
                        logger.warning(f"{market}市场未找到{account_type}类型账户")
                        continue
                    
                    acc_id = target_acc['acc_id']
                    
                    # 获取持仓
                    ret, data = ctx.position_list_query(
                        trd_env=trd_env,
                        acc_id=acc_id,
                        refresh_cache=True  # 刷新缓存以获取最新数据
                    )
                    if ret != ft.RET_OK:
                        logger.warning(f"{market}市场获取持仓失败: {data}")
                        continue
                    
                    if not data.empty:
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
                                "持仓方向": "多头" if pos.get('position_side') == ft.PositionSide.LONG else "空头",
                                "市场": market,  # 使用当前遍历的市场
                                "交易货币": pos.get('currency', ''),
                                "摊薄成本价": pos.get('diluted_cost_price', 0),
                                "平均成本价": pos.get('avg_cost_price', 0),
                            }
                            all_positions.append(position_info)
                            
                except Exception as e:
                    logger.warning(f"{market}市场获取持仓时发生错误: {e}")
                    continue
            
            return all_positions
            
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
                if isinstance(self.trade_ctx, dict):
                    for ctx in self.trade_ctx.values():
                        ctx.close()
                else:
                    self.trade_ctx.close()
                self.trade_ctx = None
                
            logger.info("富途API连接已关闭")
            
        except Exception as e:
            logger.error(f"关闭富途API连接失败: {e}")
    
    def __del__(self):
        """析构函数，确保连接被关闭"""
        self.close()

    def get_market_snapshot(self, code_list: List[str]) -> Dict[str, Any]:
        """
        获取股票快照数据
        
        Args:
            code_list: 股票代码列表,每次最多可请求400个标的
            
        Returns:
            Dict[str, Any]: 股票快照数据,包含以下字段:
            - code: 股票代码
            - name: 股票名称
            - update_time: 当前价更新时间(yyyy-MM-dd HH:mm:ss)
            - last_price: 最新价格
            - open_price: 今日开盘价
            - high_price: 最高价格
            - low_price: 最低价格
            - prev_close_price: 昨收盘价格
            - volume: 成交数量
            - turnover: 成交金额
            - turnover_rate: 换手率
            - suspension: 是否停牌
            - listing_date: 上市日期
            - equity_valid: 是否正股
            - issued_shares: 总股本
            - total_market_val: 总市值
            - net_asset: 资产净值
            - net_profit: 净利润
            - earning_per_share: 每股盈利
            - outstanding_shares: 流通股本
            - net_asset_per_share: 每股净资产
            - circular_market_val: 流通市值
            - pe_ratio: 市盈率
            - pe_ttm_ratio: 市盈率(TTM)
            - pb_ratio: 市净率
            - dividend_ttm: 股息(TTM)
            - dividend_ratio_ttm: 股息率(TTM)
            - amplitude: 振幅
            - avg_price: 平均价
            - bid_ask_ratio: 委比
            - volume_ratio: 量比
            - highest_52weeks_price: 52周最高价
            - lowest_52weeks_price: 52周最低价
            - highest_history_price: 历史最高价
            - lowest_history_price: 历史最低价
        """
        try:
            if not self.quote_ctx:
                raise Exception("行情API未连接")
            
            # 限制每次请求的标的数量
            if len(code_list) > 400:
                raise Exception("每次最多可请求400个标的")
            
            # 获取快照数据
            ret, data = self.quote_ctx.get_market_snapshot(code_list)
            if ret != ft.RET_OK:
                raise Exception(f"获取快照数据失败: {data}")
            
            if data.empty:
                return {}
            
            snapshots = []
            for _, snapshot in data.iterrows():
                snapshot_info = {
                    "股票代码": snapshot.get('code', ''),
                    "股票名称": snapshot.get('stock_name', ''),
                    "更新时间": snapshot.get('update_time', ''),
                    "最新价": snapshot.get('last_price', 0),
                    "开盘价": snapshot.get('open_price', 0),
                    "最高价": snapshot.get('high_price', 0),
                    "最低价": snapshot.get('low_price', 0),
                    "昨收价": snapshot.get('prev_close_price', 0),
                    "成交量": snapshot.get('volume', 0),
                    "成交额": snapshot.get('turnover', 0),
                    "换手率": f"{snapshot.get('turnover_rate', 0):.2f}%",
                    "是否停牌": snapshot.get('suspension', False),
                    "上市日期": snapshot.get('listing_date', ''),
                    "总股本": snapshot.get('issued_shares', 0),
                    "总市值": snapshot.get('total_market_val', 0),
                    "资产净值": snapshot.get('net_asset', 0),
                    "净利润": snapshot.get('net_profit', 0),
                    "每股盈利": snapshot.get('earning_per_share', 0),
                    "流通股本": snapshot.get('outstanding_shares', 0),
                    "每股净资产": snapshot.get('net_asset_per_share', 0),
                    "流通市值": snapshot.get('circular_market_val', 0),
                    "市盈率": snapshot.get('pe_ratio', 0),
                    "市盈率(TTM)": snapshot.get('pe_ttm_ratio', 0),
                    "市净率": snapshot.get('pb_ratio', 0),
                    "股息(TTM)": snapshot.get('dividend_ttm', 0),
                    "股息率(TTM)": f"{snapshot.get('dividend_ratio_ttm', 0):.2f}%",
                    "振幅": f"{snapshot.get('amplitude', 0):.2f}%",
                    "平均价": snapshot.get('avg_price', 0),
                    "委比": f"{snapshot.get('bid_ask_ratio', 0):.2f}%",
                    "量比": snapshot.get('volume_ratio', 0),
                    "52周最高价": snapshot.get('highest_52weeks_price', 0),
                    "52周最低价": snapshot.get('lowest_52weeks_price', 0),
                    "历史最高价": snapshot.get('highest_history_price', 0),
                    "历史最低价": snapshot.get('lowest_history_price', 0),
                }
                snapshots.append(snapshot_info)
            
            return {"快照数据": snapshots}
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"获取快照数据失败: {e}")
            return {} 