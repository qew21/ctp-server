import React, { useState, useEffect } from 'react';
import api from '../../utils/Request';
import { useRefresh } from '../../utils/Context';
import { Table } from 'antd';

const TradesTable = () => {
    const { refreshToken } = useRefresh();
    
    const onChange = (pagination, filters, sorter, extra) => {
        console.log('params', pagination, filters, sorter, extra);
    };

    const [trades, setTrades] = useState([]);

    useEffect(() => {
        const fetchTrades = async () => {
            api.get('/get_trades')
                .then(res => {
                    const tradesList = Object.entries(res.data[0]).map(([key, value]) => ({
                        'trade_id': key,
                        ...value
                    }));
                    setTrades(tradesList);
                })
                .catch(error => {
                    console.error(error);
                });

        };

        fetchTrades();
    }, [refreshToken]);

    const columns = [
        {
            title: '成交单号',
            dataIndex: 'trade_id',
            sorter: (a, b) => a.trade_id.localeCompare(b.trade_id),
        },
        {
            title: '合约',
            dataIndex: 'code',
            sorter: (a, b) => a.code.localeCompare(b.code),
        },
        {
            title: '方向',
            dataIndex: 'direction',
            sorter: (a, b) => a.direction.localeCompare(b.direction),
        },
        {
            title: '挂单单号',
            dataIndex: 'order_id',
            sorter: (a, b) => a.order_id.localeCompare(b.order_id),
        },
        {
            title: '数目',
            dataIndex: 'volume',
            sorter: (a, b) => a.volume - b.volume,
        },
        {
            title: '价格',
            dataIndex: 'price',
            sorter: (a, b) => a.price - b.price,
        },
        {
            title: '成交日期',
            dataIndex: 'trade_date',
            sorter: (a, b) => a.insert_time.localeCompare(b.insert_time),
        },
        {
            title: '成交时间',
            dataIndex: 'trade_time',
            sorter: (a, b) => a.trade_time.localeCompare(b.trade_time),
        }
    ];

    return <Table columns={columns} dataSource={trades} onChange={onChange} pagination={trades.length > 10}/>;
}
export default TradesTable;