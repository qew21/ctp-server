import React, { useState, useEffect } from 'react';
import api from '../../utils/Request';
import { useRefresh } from '../../utils/Context';
import { Table } from 'antd';

const AccountTable = () => {
    const { refreshToken } = useRefresh();

    const onChange = (pagination, filters, sorter, extra) => {
        console.log('params', pagination, filters, sorter, extra);
    };

    const [account, setAccount] = useState([]);

    useEffect(() => {
        const fetchAccount = async () => {
            api.get('/get_account')
                .then(res => {
                    setAccount([res.data[0]]);
                })
                .catch(error => {
                    console.error(error);
                });

        };

        fetchAccount();
    }, [refreshToken]);

    const columns = [
        {
            title: '账户总额',
            dataIndex: 'balance',
        },
        {
            title: '持仓市值',
            dataIndex: 'margin',
        },
        {
            title: '可用资金',
            dataIndex: 'available',
        },
        {
            title: '当日利润',
            dataIndex: 'profit',
        },
    ];

    return <Table columns={columns} dataSource={account} onChange={onChange} pagination={false} />;
}
export default AccountTable;