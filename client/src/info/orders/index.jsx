import React, { useState, useEffect } from 'react';
import api from '../../utils/Request';
import { useRefresh } from '../../utils/Context';
import { Table, Button } from 'antd';

const OrdersTable = () => {
    const { refreshToken } = useRefresh();

    const onChange = (pagination, filters, sorter, extra) => {
        console.log('params', pagination, filters, sorter, extra);
    };

    const [orders, setOrders] = useState([]);

    const fetchOrders = async () => {
        api.get('/get_orders')
            .then(res => {
                const ordersList = Object.entries(res.data[0]).map(([key, value]) => ({
                    'order_id': key,
                    ...value,
                }));
                setOrders(ordersList);
            })
            .catch(error => {
                console.error(error);
            });
    };

    useEffect(() => {
        fetchOrders();
    }, [refreshToken]);

    const handleCancelOrder = async (orderId) => {
        try {
            api.get(`/order_delete?order_id=${orderId}`)
                .then(res => {
                    console.log(res.data);
                    fetchOrders();
                })
                .catch(error => {
                    console.error(error);
                });
        } catch (error) {
            console.error(error);
        }
    };

    const columns = [
        {
            title: '挂单单号',
            dataIndex: 'order_id',
            sorter: (a, b) => a.order_id.localeCompare(b.order_id),
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
            title: '下单时间',
            dataIndex: 'insert_time',
            sorter: (a, b) => a.insert_time.localeCompare(b.insert_time),
        },
        {
            title: '撤单时间',
            dataIndex: 'cancel_time',
            sorter: (a, b) => a.cancel_time.localeCompare(b.cancel_time),
        },
        {
            title: '成交量',
            dataIndex: 'volume_traded',
            sorter: (a, b) => a.volume_traded - b.volume_traded,
        },
        {
            title: '操作',
            dataIndex: 'active',
            key: 'action',
            render: (text, record) => {
                return record.is_active ? (
                    <Button type="link" style={{ padding: 0, margin: 0, border: 'none', boxShadow: 'none' }} onClick={handleCancelOrder(record.order_id)}>撤单</Button>
                ) : null;
            }
        },
    ];

    return <Table columns={columns} dataSource={orders} onChange={onChange} pagination={orders.length > 10} />;
}
export default OrdersTable;