import React, { useState, useEffect } from 'react';
import { AutoComplete, Radio, Select, InputNumber, Button, message, Table } from 'antd';
import api from '../utils/Request';
import { useRefresh } from '../utils/Context';



const OrderForm = () => {
    const { triggerRefresh } = useRefresh();
    const [instruments, setInstruments] = useState([]);
    const [name, setName] = useState('');
    const [direction, setDirection] = useState('long');
    const [priceType, setPriceType] = useState('market');
    const [price, setPrice] = useState('');
    const [volume, setVolume] = useState(1);
    const [levelPrices, setLevelPrices] = useState({});
    const [autoCompleteOptions, setAutoCompleteOptions] = useState(instruments.map(name => ({ value: name })));

    const handleNameSearch = value => {
        setName(value);

        const filteredAndSortedInstruments = instruments
            .filter(name => name.includes(value))
            .sort((a, b) => {
                if (a.startsWith(value) && b.startsWith(value)) {
                    return a.localeCompare(b);
                }
                if (a.startsWith(value)) {
                    return -1;
                }
                if (b.startsWith(value)) {
                    return 1;
                }
                return a.localeCompare(b);
            });

        setAutoCompleteOptions(filteredAndSortedInstruments.map(name => ({ value: name })));
    };


    const handleNameSelect = value => {
        setName(value);
        const fetchPoints = async () => {
            api.get(`/query_points?code=${value}`)
                .then(res => {
                    console.log(res.data);
                    setLevelPrices(res.data);
                })
                .catch(error => {
                    console.error(error);
                });

        };
        fetchPoints();
    };

    useEffect(() => {
        const fetchInstruments = async () => {
            api.get('/get_instruments')
                .then(res => {
                    setInstruments(res.data);
                    setAutoCompleteOptions(res.data.map(name => ({ value: name })));
                })
                .catch(error => {
                    console.error(error);
                });

        };

        fetchInstruments();
    }, []);

    const columns = [
        {
            title: 'Level',
            dataIndex: 'level',
            key: 'level',
        },
        {
            title: 'Bid',
            dataIndex: 'bid',
            key: 'bid',
            render: bid => <a onClick={() => setPrice(bid[0])}>{`${bid[0]} (${bid[1]})`}</a>, // 显示为 "价格 (数量)"
        },
        {
            title: 'Ask',
            dataIndex: 'ask',
            key: 'ask',
            render: ask => <a onClick={() => setPrice(ask[0])}>{`${ask[0]} (${ask[1]})`}</a>, // 显示为 "价格 (数量)"
        },
    ];

    const data = [
        { key: '1', level: '1', bid: levelPrices.bid1, ask: levelPrices.ask1 },
        { key: '2', level: '2', bid: levelPrices.bid2, ask: levelPrices.ask2 },
        { key: '3', level: '3', bid: levelPrices.bid3, ask: levelPrices.ask3 },
        { key: '4', level: '4', bid: levelPrices.bid4, ask: levelPrices.ask4 },
        { key: '5', level: '5', bid: levelPrices.bid5, ask: levelPrices.ask5 },
    ];

    const handleSubmit = async () => {
        try {
            if (priceType === 'market') {
                api.get(`/order_market?code=${name}&direction=${direction}&volume=${volume}`)
                    .then(res => {
                        message.success(`下单成功 ${JSON.stringify(res.data, null, 2)}`);
                        triggerRefresh();
                    })
                    .catch(error => {
                        message.success(`下单失败 ${error}`);
                    });
            } else {
                api.get(`/order_limit?code=${name}&direction=${direction}&volume=${volume}&price=${price}`)
                    .then(res => {
                        message.success(`下单成功 ${JSON.stringify(res.data, null, 2)}`);
                        triggerRefresh();
                    })
                    .catch(error => {
                        message.success(`下单失败 ${error}`);
                    });
            }
            console.log(name, direction, priceType, price, volume);
        } catch (error) {
            message.error(`下单失败 ${error}`);
        }
    };

    return (
        
        <div style={{ padding: 20 }}>
            <AutoComplete
                style={{ width: 200, marginBottom: 16, marginRight: 8 }}
                options={autoCompleteOptions}
                onSelect={handleNameSelect}
                onSearch={handleNameSearch}
                placeholder="输入或搜索合约名称"
                value={name}
            />
            <Radio.Group onChange={e => setDirection(e.target.value)} value={direction} style={{ marginBottom: 16 }}>
                <Radio value="long">long</Radio>
                <Radio value="short">short</Radio>
            </Radio.Group>
            <Select defaultValue="market" style={{ width: 80, marginRight: 8, marginBottom: 16 }} onChange={setPriceType} >
                <Select.Option value="market">市价</Select.Option>
                <Select.Option value="limit">限价</Select.Option>
            </Select>
            {priceType === 'limit' && (
                <InputNumber
                    style={{ width: 200, marginRight: 8, marginBottom: 16 }}
                    addonBefore="价格"
                    value={price}
                    min={0}
                    step={0.02}
                    onChange={value => setPrice(value)}
                />
            )}
            数目
            <InputNumber
                style={{ width: 80, marginLeft: 8, marginRight: 8, marginBottom: 16 }}
                min={1}
                value={volume}
                onChange={value => setVolume(value)}
            />
            <Button type="primary" onClick={handleSubmit} style={{ marginBottom: 16 }}>
                确认
            </Button>
            <br />
            {Object.keys(levelPrices).length > 0 && (
                <Table columns={columns} dataSource={data} pagination={false} />
            )}
        </div>
        
    );
};

export default OrderForm;
