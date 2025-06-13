#!/usr/bin/env python3
"""
富途API客户端

基于富途OpenAPI实现的客户端，提供股票数据和交易功能。
文档: https://openapi.futunn.com/futu-api-doc/
"""

import logging
import time
from typing import Dict, List, Optional, Any, Union, Callable
import futu as ft
from datetime import datetime, timedelta
import pandas as pd
from futu import ModifyOrderOp, TrdEnv

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
                            logger.info(f"富途{market}交易API连接成功")
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

    def get_positions(self, account_type: str = "REAL") -> str:
        """获取持仓信息"""
        try:
            if not self.trade_ctx:
                return "❌ 交易API未连接，请先解锁交易"
            
            # 转换账户类型
            env_map = {
                "REAL": ft.TrdEnv.REAL,
                "SIMULATE": ft.TrdEnv.SIMULATE
            }
            
            # 获取持仓数据
            ret, data = self.trade_ctx['HK'].position_list_query(
                trd_env=env_map.get(account_type, ft.TrdEnv.REAL)
            )
            
            if ret != ft.RET_OK:
                return f"❌ 获取持仓数据失败: {data}"
            
            if data.empty:
                return f"📊 {account_type} 账户暂无持仓"
            
            # 格式化输出
            text_output = f"📊 {account_type} 持仓信息\n"
            text_output += "=" * 50 + "\n\n"
            
            # 计算总资产和总盈亏
            total_pl = 0
            total_value = 0
            
            # 遍历每个持仓
            for _, position in data.iterrows():
                code = position.get('code', '')
                name = position.get('stock_name', '')
                qty = position.get('qty', 0)
                cost_price = position.get('cost_price', 0)
                current_price = position.get('current_price', 0)
                market_val = position.get('market_val', 0)
                pl_val = position.get('pl_val', 0)
                pl_ratio = position.get('pl_ratio', 0) * 100  # 转换为百分比
                
                # 累计总盈亏和总市值
                total_pl += pl_val
                total_value += market_val
                
                # 选择emoji
                emoji = "📈" if pl_val > 0 else "📉" if pl_val < 0 else "➡️"
                
                # 添加持仓信息
                text_output += f"{emoji} {code} - {name}\n"
                text_output += f"   持仓: {qty:,.0f} 股\n"
                text_output += f"   成本价: {cost_price:.3f} | 现价: {current_price:.3f}\n"
                text_output += f"   市值: {market_val:,.2f}\n"
                text_output += f"   盈亏: {pl_val:+,.2f} ({pl_ratio:+.2f}%)\n\n"
            
            # 添加总计信息
            text_output += "📈 总计\n"
            text_output += f"   总市值: {total_value:,.2f}\n"
            text_output += f"   总盈亏: {total_pl:+,.2f}\n"
            
            return text_output
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"获取持仓数据失败: {e}")
            return f"❌ 获取持仓数据失败: {str(e)}"
    

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
            return {"error": str(e)}

    def get_history_kline(self, code: str, start: str = None, end: str = None, 
                         ktype: str = 'K_DAY', autype: str = 'QFQ') -> Dict[str, Any]:
        """
        获取历史K线数据
        
        Args:
            code: 股票代码，如 US.AAPL, HK.00700
            start: 开始时间，格式：yyyy-MM-dd，如：2023-01-01
            end: 结束时间，格式：yyyy-MM-dd，如：2023-12-31
            ktype: K线类型，支持：K_1M, K_5M, K_15M, K_30M, K_60M, K_DAY, K_WEEK, K_MONTH
            autype: 复权类型，支持：None(不复权), QFQ(前复权), HFQ(后复权)
            
        Returns:
            Dict[str, Any]: K线数据字典
        """
        try:
            if not self.quote_ctx:
                raise Exception("行情API未连接")
            
            # 转换K线类型
            ktype_map = {
                'K_1M': ft.KLType.K_1M,
                'K_5M': ft.KLType.K_5M,
                'K_15M': ft.KLType.K_15M,
                'K_30M': ft.KLType.K_30M,
                'K_60M': ft.KLType.K_60M,
                'K_DAY': ft.KLType.K_DAY,
                'K_WEEK': ft.KLType.K_WEEK,
                'K_MONTH': ft.KLType.K_MON
            }
            
            # 转换复权类型
            autype_map = {
                'None': ft.AuType.NONE,
                'QFQ': ft.AuType.QFQ,
                'HFQ': ft.AuType.HFQ
            }
            
            # 获取K线数据
            ret, data, page_req_key = self.quote_ctx.request_history_kline(
                code=code,
                start=start,
                end=end,
                ktype=ktype_map.get(ktype, ft.KLType.K_DAY),
                autype=autype_map.get(autype, ft.AuType.QFQ),
                max_count=1000,  # 单次最多返回1000根K线
                extended_time=True  # 允许美股盘前盘后数据
            )
            
            if ret != ft.RET_OK:
                # 解析股票代码的市场
                market = code.split('.')[0] if '.' in code else ''
                error_msg = []
                
                # 添加错误信息
                error_msg.append(f"获取K线失败: {data}")
                error_msg.append(f"市场: {market}")
                
                # 添加市场特定提示
                if market == 'US':
                    error_msg.append("请检查美股行情权限和交易时段（美东时间9:30-16:00）")
                    error_msg.append("如需美股LV2行情，请订阅：https://qtcard.futunn.com/intro/uslv2")
                elif market == 'HK':
                    error_msg.append("请检查港股行情权限和交易时段（香港时间9:30-16:00）")
                elif market in ['SH', 'SZ']:
                    error_msg.append("请检查A股行情权限和交易时段（北京时间9:30-15:00）")
                    
                return {"error": "\n".join(error_msg)}

            if data.empty:
                return {"error": "未获取到K线数据"}

            # 格式化K线数据
            klines = []
            for _, kline in data.iterrows():
                kline_info = {
                    "时间": kline.get('time_key', ''),
                    "开盘": kline.get('open', 0),
                    "收盘": kline.get('close', 0),
                    "最高": kline.get('high', 0),
                    "最低": kline.get('low', 0),
                    "成交量": kline.get('volume', 0),
                    "成交额": kline.get('turnover', 0),
                }
                
                # 添加额外指标（如果有）
                if 'turnover_rate' in data.columns:
                    kline_info["换手率"] = kline.get('turnover_rate', 0)
                if 'pe_ratio' in data.columns:
                    kline_info["市盈率"] = kline.get('pe_ratio', 0)
                if 'pb_ratio' in data.columns:
                    kline_info["市净率"] = kline.get('pb_ratio', 0)
                
                klines.append(kline_info)
            
            # === 技术指标计算 ===
            tech = {}
            if len(klines) >= 26:
                df = pd.DataFrame(klines)
                df['EMA12'] = df['收盘'].ewm(span=12, adjust=False).mean()
                df['EMA26'] = df['收盘'].ewm(span=26, adjust=False).mean()
                df['DIF'] = df['EMA12'] - df['EMA26']
                df['DEA'] = df['DIF'].ewm(span=9, adjust=False).mean()
                df['MACD'] = 2 * (df['DIF'] - df['DEA'])
                # MACD信号
                macd_signals = []
                for i in range(1, len(df)):
                    if df['DIF'].iloc[i-1] < df['DEA'].iloc[i-1] and df['DIF'].iloc[i] > df['DEA'].iloc[i]:
                        macd_signals.append({'date': df['时间'].iloc[i], 'signal': '金叉'})
                    elif df['DIF'].iloc[i-1] > df['DEA'].iloc[i-1] and df['DIF'].iloc[i] < df['DEA'].iloc[i]:
                        macd_signals.append({'date': df['时间'].iloc[i], 'signal': '死叉'})
                # 布林带
                df['MB'] = df['收盘'].rolling(window=20).mean()
                df['STD'] = df['收盘'].rolling(window=20).std()
                df['UP'] = df['MB'] + 2 * df['STD']
                df['DN'] = df['MB'] - 2 * df['STD']
                # 压力/支撑位
                levels = {
                    'year_high': df['最高'].max(),
                    'year_low': df['最低'].min(),
                    'ma20': df['收盘'].rolling(window=20).mean().iloc[-1],
                    'ma60': df['收盘'].rolling(window=60).mean().iloc[-1]
                }
                tech = {
                    'macd': {
                        'latest': {
                            'DIF': df['DIF'].iloc[-1],
                            'DEA': df['DEA'].iloc[-1],
                            'MACD': df['MACD'].iloc[-1]
                        },
                        'signals': macd_signals[-5:]
                    },
                    'boll': {
                        'UP': df['UP'].iloc[-1],
                        'MB': df['MB'].iloc[-1],
                        'DN': df['DN'].iloc[-1]
                    },
                    'levels': levels
                }

            # 计算统计数据
            if klines:
                first_kline = klines[0]
                last_kline = klines[-1]
                total_change = (last_kline['收盘'] - first_kline['开盘']) / first_kline['开盘'] * 100
                
                stats = {
                    "K线数量": len(klines),
                    "起始日期": first_kline['时间'],
                    "结束日期": last_kline['时间'],
                    "总涨跌幅": total_change,
                    "最高价": max(k['最高'] for k in klines),
                    "最低价": min(k['最低'] for k in klines),
                    "总成交量": sum(k['成交量'] for k in klines),
                    "平均成交量": sum(k['成交量'] for k in klines) / len(klines),
                }
                
                # 如果有换手率数据，计算平均换手率
                if all('换手率' in k for k in klines):
                    stats["平均换手率"] = sum(k['换手率'] for k in klines) / len(klines)
                
                return {
                    "股票代码": code,
                    "K线类型": ktype,
                    "复权类型": autype,
                    "统计数据": stats,
                    "K线数据": klines,
                    "技术指标": tech
                }
            else:
                return {"error": "未获取到K线数据"}
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"获取历史K线失败: {e}")
            return {"error": str(e)}

    def get_funds(self, trd_env: str = "REAL", acc_id: int = 0, refresh_cache: bool = False) -> Dict[str, Any]:
        """
        查询账户资金
        
        Args:
            trd_env: 交易环境，REAL（真实）或 SIMULATE（模拟）
            acc_id: 交易业务账户ID，默认0表示使用第一个账户
            refresh_cache: 是否刷新缓存，默认False
            
        Returns:
            Dict[str, Any]: 账户资金信息
        """
        try:
            if not self.trade_ctx:
                return {"error": "交易API未连接，请先解锁交易"}
            
            # 转换交易环境
            env_map = {
                "REAL": ft.TrdEnv.REAL,
                "SIMULATE": ft.TrdEnv.SIMULATE
            }
            
            # 获取资金数据
            ret, data = self.trade_ctx['HK'].accinfo_query(
                trd_env=env_map.get(trd_env, ft.TrdEnv.REAL),
                acc_id=acc_id,
                refresh_cache=refresh_cache
            )
            
            if ret != ft.RET_OK:
                return {"error": f"获取资金数据失败: {data}"}
            
            if data.empty:
                return {"error": "未获取到资金数据"}
            
            # 格式化资金数据
            funds = data.iloc[0]
            result = {
                "总资产": {
                    "总资产净值": float(funds.get('total_assets', 0)),
                    "证券资产": float(funds.get('securities_assets', 0)),
                    "基金资产": float(funds.get('funds_assets', 0)),
                    "债券资产": float(funds.get('bonds_assets', 0)),
                },
                "现金信息": {},
                "交易能力": {
                    "最大购买力": float(funds.get('power', 0)),
                    "卖空购买力": float(funds.get('max_power_short', 0)),
                },
                "风险信息": {
                    "初始保证金": float(funds.get('initial_margin', 0)),
                    "维持保证金": float(funds.get('maintenance_margin', 0)),
                    "保证金追缴金额": float(funds.get('margin_call_margin', 0)),
                    "风险状态": self._convert_risk_status(funds.get('risk_status', 0))
                }
            }
            
            # 添加各币种现金信息
            cash_info_list = funds.get('cash_info_list', [])
            if not isinstance(cash_info_list, list):
                cash_info_list = []
                
            currency_map = {
                1: "港币",  # HKD
                2: "美元",  # USD
                3: "离岸人民币",  # CNH
                4: "在岸人民币",  # CNY
                5: "日元",   # JPY
                6: "新加坡元"  # SGD
            }
            
            for cash_info in cash_info_list:
                currency = currency_map.get(cash_info.get('currency', 0), '未知货币')
                result["现金信息"][currency] = {
                    "现金": float(cash_info.get('cash', 0)),
                    "可用资金": float(cash_info.get('available_balance', 0)),
                    "购买力": float(cash_info.get('net_cash_power', 0))
                }
            
            return result
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"获取资金数据失败: {e}")
            return {"error": str(e)}
            
    def _convert_risk_status(self, status: int) -> str:
        """转换风险状态为可读字符串"""
        status_map = {
            1: "正常",
            2: "关注",
            3: "警告",
            4: "追保",
            5: "强平",
            6: "禁买",
            7: "禁卖",
            8: "禁买卖"
        }
        return status_map.get(status, "未知状态")

    def place_order(self, price: float, qty: float, code: str, trd_side: str,
                   order_type: str = "NORMAL", adjust_limit: float = 0,
                   trd_env: str = "REAL", acc_id: int = 0,
                   remark: str = None, time_in_force: str = "DAY",
                   fill_outside_rth: bool = False) -> Dict[str, Any]:
        """
        下单
        
        Args:
            price: 订单价格，即使是市价单也需要传入价格（可以是任意值）
            qty: 订单数量，期权期货单位是"张"
            code: 股票代码，如 US.AAPL, HK.00700
            trd_side: 交易方向，BUY买入，SELL卖出，SELL_SHORT卖空，BUY_BACK买回
            order_type: 订单类型，默认NORMAL正常限价单
            adjust_limit: 价格微调幅度，正数代表向上调整，负数代表向下调整
            trd_env: 交易环境，REAL（真实）或 SIMULATE（模拟）
            acc_id: 交易业务账户ID，默认0表示使用第一个账户
            remark: 备注，订单会带上此备注字段，方便标识订单
            time_in_force: 订单有效期，默认DAY当日有效
            fill_outside_rth: 是否允许盘前盘后成交，用于港股盘前竞价与美股盘前盘后
            
        Returns:
            Dict[str, Any]: 下单结果，包含订单号等信息
        """
        try:
            if not self.trade_ctx:
                return {"error": "交易API未连接，请先解锁交易"}
            
            # 转换交易环境
            env_map = {
                "REAL": ft.TrdEnv.REAL,
                "SIMULATE": ft.TrdEnv.SIMULATE
            }
            
            # 转换交易方向
            side_map = {
                "BUY": ft.TrdSide.BUY,
                "SELL": ft.TrdSide.SELL,
                "SELL_SHORT": ft.TrdSide.SELL_SHORT,
                "BUY_BACK": ft.TrdSide.BUY_BACK
            }
            
            # 转换订单类型
            type_map = {
                "NORMAL": ft.OrderType.NORMAL,
                "MARKET": ft.OrderType.MARKET,
                "ABSOLUTE_LIMIT": ft.OrderType.ABSOLUTE_LIMIT,
                "AUCTION": ft.OrderType.AUCTION,
                "AUCTION_LIMIT": ft.OrderType.AUCTION_LIMIT,
                "SPECIAL_LIMIT": ft.OrderType.SPECIAL_LIMIT
            }
            
            # 转换订单有效期
            time_map = {
                "DAY": ft.TimeInForce.DAY,
                "GTC": ft.TimeInForce.GTC
            }
            
            # 获取市场信息
            market = code.split('.')[0] if '.' in code else ''
            if market not in ['HK', 'US', 'SH', 'SZ']:
                return {"error": "不支持的市场代码"}
                
            # 选择对应市场的交易上下文
            market_map = {
                'HK': 'HK',
                'US': 'US',
                'SH': 'CN',
                'SZ': 'CN'
            }
            trade_ctx = self.trade_ctx.get(market_map[market])
            if not trade_ctx:
                return {"error": f"未找到{market}市场的交易上下文"}
            
            # 下单
            ret, data = trade_ctx.place_order(
                price=price,
                qty=qty,
                code=code,
                trd_side=side_map.get(trd_side),
                order_type=type_map.get(order_type, ft.OrderType.NORMAL),
                adjust_limit=adjust_limit,
                trd_env=env_map.get(trd_env, ft.TrdEnv.REAL),
                acc_id=acc_id,
                remark=remark,
                time_in_force=time_map.get(time_in_force, ft.TimeInForce.DAY),
                fill_outside_rth=fill_outside_rth
            )
            
            if ret != ft.RET_OK:
                error_msg = []
                error_msg.append(f"下单失败: {data}")
                
                # 添加市场特定提示
                if market == 'US':
                    error_msg.append("请检查美股交易时段（美东时间9:30-16:00）")
                elif market == 'HK':
                    error_msg.append("请检查港股交易时段（香港时间9:30-16:00）")
                elif market in ['SH', 'SZ']:
                    error_msg.append("请检查A股交易时段（北京时间9:30-15:00）")
                    
                return {"error": "\n".join(error_msg)}
            
            order_info = {
                "订单号": str(data.iloc[0].get('order_id', '')),
                "代码": code,
                "方向": trd_side,
                "价格": price,
                "数量": qty,
                "类型": order_type,
                "状态": "已提交",
                "备注": remark or ""
            }
            
            return {"success": True, "data": order_info}
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"下单失败: {e}")
            return {"error": str(e)}

    def modify_order(self, modify_order_op, order_id, qty=0, price=0, adjust_limit=0, trd_env="REAL", acc_id=0):
        op_map = {"NORMAL": ModifyOrderOp.NORMAL, "CANCEL": ModifyOrderOp.CANCEL}
        env_map = {"REAL": TrdEnv.REAL, "SIMULATE": TrdEnv.SIMULATE}
        try:
            ctx = self.trade_ctx['HK']  # 这里只以港股为例，如需支持美股/其他市场可扩展
            ret, data = ctx.modify_order(
                modify_order_op=op_map.get(modify_order_op, ModifyOrderOp.NORMAL),
                order_id=order_id,
                qty=qty,
                price=price,
                adjust_limit=adjust_limit,
                trd_env=env_map.get(trd_env, TrdEnv.REAL),
                acc_id=acc_id
            )
            if ret == 0:
                return data.to_dict(orient='records')
            else:
                return {"error": str(data)}
        except Exception as e:
            return {"error": str(e)}

    def get_stock_filter(self, market, filter_list, plate_code=None, begin=0, num=200):
        """
        条件选股，filter_list 必须为 futu.SimpleFilter 对象列表，stock_field 用 StockField 枚举。
        Args:
            market: str 或 futu.Market，如 'HK'/'US'/'SH'/'SZ' 或对应的 futu.Market 枚举
            filter_list: [futu.SimpleFilter, ...]，stock_field 必须用 futu.StockField 枚举
            plate_code: 板块代码，可选，如 'HK.Motherboard'（港股主板）
            begin: 起始序号，默认0
            num: 返回数量，默认200，最大200
        Returns:
            list[dict] or {"error": str}
        """
        import futu as ft
        try:
            if not self.quote_ctx:
                return {"error": "行情API未连接"}

            # 验证 filter_list 中的元素类型
            for f in filter_list:
                if not isinstance(f, (ft.SimpleFilter, ft.FinancialFilter, ft.CustomIndicatorFilter)):
                    return {"error": "filter_list 内元素必须为 SimpleFilter、FinancialFilter 或 CustomIndicatorFilter 对象"}

            # 初始化结果列表
            all_results = []
            current_begin = begin
            last_page = False

            while not last_page and (num == 0 or len(all_results) < num):
                # 计算本次请求数量
                request_num = num - len(all_results) if num > 0 else 200
                request_num = min(request_num, 200)  # 每次最多请求200条

                # 发起请求
                ret, data = self.quote_ctx.get_stock_filter(
                    market=market,
                    filter_list=filter_list,
                    plate_code=plate_code,
                    begin=current_begin,
                    num=request_num
                )

                if ret != ft.RET_OK:
                    return {"error": str(data)}

                # 解析返回数据
                last_page, all_count, stock_list = data

                # 处理本页数据
                for stock in stock_list:
                    # 构建基本信息
                    stock_dict = {
                        'code': stock.stock_code,  # 股票代码
                        'name': stock.stock_name,  # 股票名称
                        'market': market  # 市场
                    }

                    # 添加筛选字段的值
                    for f in filter_list:
                        if isinstance(f, ft.SimpleFilter):
                            stock_dict[ft.StockField.to_string(f.stock_field)] = stock[f]
                        elif isinstance(f, ft.FinancialFilter):
                            stock_dict[ft.StockField.to_string(f.stock_field)] = stock[f]
                        elif isinstance(f, ft.CustomIndicatorFilter):
                            stock_dict['custom_indicator'] = stock[f]

                    all_results.append(stock_dict)

                # 更新开始位置
                current_begin += len(stock_list)

                # 如果达到请求数量或者是最后一页，结束循环
                if num > 0 and len(all_results) >= num:
                    break
                if last_page:
                    break

                # 添加延时避免触发限频
                time.sleep(3)

            return all_results

        except Exception as e:
            self.last_error = str(e)
            logger.error(f"条件选股失败: {e}")
            return {"error": str(e)} 