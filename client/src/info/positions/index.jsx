import React, { useState, useEffect } from 'react';
import api from '../../utils/Request';
import { useRefresh } from '../../utils/Context';
import { Table } from 'antd';

const PositionsTable = () => {
    const { refreshToken } = useRefresh();

    const onChange = (pagination, filters, sorter, extra) => {
        console.log('params', pagination, filters, sorter, extra);
    };

    const [positions, setPositions] = useState([]);

    useEffect(() => {
        const fetchPositions = async () => {
            api.get('/get_position')
                .then(res => {
                    setPositions(res.data[0]);
                })
                .catch(error => {
                    console.error(error);
                });

        };

        fetchPositions();
    }, [refreshToken]);
    const columns = [
        {
            title: '持仓合约',
            dataIndex: 'code',
            sorter: (a, b) => a.code.localeCompare(b.code),
        },
        {
            title: '方向',
            dataIndex: 'direction',
            sorter: (a, b) => a.direction.localeCompare(b.direction),
        },
        {
            title: '持仓量',
            dataIndex: 'volume',
            sorter: (a, b) => a.volume - b.volume,
        },
        {
            title: '市值',
            dataIndex: 'margin',
            sorter: (a, b) => a.margin - b.margin,
        },

        {
            title: '当前价',
            dataIndex: 'settlement_price',
            sorter: (a, b) => a.settlement_price - b.settlement_price,
        },
        {
            title: '开仓价',
            dataIndex: 'open_cost_price',
            sorter: (a, b) => a.open_cost_price - b.open_cost_price,
        },
        {
            title: '持仓盈亏',
            dataIndex: 'profit',
            sorter: (a, b) => a.profit - b.profit,
        },
        {
            title: '持仓成本',
            dataIndex: 'cost',
            sorter: (a, b) => a.cost - b.cost,
        },
        {
            title: '开仓量',
            dataIndex: 'open_volume',
            sorter: (a, b) => a.open_volume - b.open_volume,
        },
        {
            title: '平仓量',
            dataIndex: 'close_volume',
            sorter: (a, b) => a.close_volume - b.close_volume,
        },
        {
            title: '昨仓量',
            dataIndex: 'yd_position',
            sorter: (a, b) => a.yd_position - b.yd_position,
        },
        {
            title: '新开量',
            dataIndex: 'today_position',
            sorter: (a, b) => a.today_position - b.today_position,
        },
    ];

    return <Table columns={columns} dataSource={positions} onChange={onChange} pagination={positions.length > 10} />;
}
export default PositionsTable;