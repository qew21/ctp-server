import React, { useState, useEffect } from 'react';
import { RefreshProvider } from './utils/Context';
import { Menu, Row, Col, Affix } from 'antd';
import './App.css';
import AccountTable from './info/account';
import PositionsTable from './info/positions';
import OrdersTable from './info/orders';
import TradesTable from './info/trades';
import OrderForm from './order';

function App() {
  const [activeKey, setActiveKey] = useState('account');
  const contentRef = React.useRef(null);

  useEffect(() => {
    document.title = "CTP Server"; 
    const handleScroll = () => {
      const currentId = [...contentRef.current.children].find((child) =>
        child.offsetTop <= window.scrollY + window.innerHeight &&
        child.offsetTop + child.offsetHeight > window.scrollY
      ).id;
      if (currentId !== activeKey) {
        setActiveKey(currentId);
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [activeKey]);
  const onMenuClick = ({ key }) => {
    setActiveKey(key);
    const elementId = key === 'account' ? 'account' : 
                    key === 'positions' ? 'positions' : 
                    key === 'orders' ? 'orders' : 
                    'trades';
    document.getElementById(elementId).scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <RefreshProvider>
     <div style={{ overflow: 'auto' }}>
        <Row>
      <Col  flex="none">
          <Affix>
            <Menu
              mode="inline"
              selectedKeys={[activeKey]}
              items={[
                {
                  key: 'account',
                  label: '账户信息',
                  onClick: onMenuClick,
                },
                {
                  key: 'positions',
                  label: '持仓信息',
                  onClick: onMenuClick,
                },
                {
                  key: 'orders',
                  label: '订单信息',
                  onClick: onMenuClick,
                },
                {
                  key: 'trades',
                  label: '交易记录',
                  onClick: onMenuClick,
                },
                {
                  key: 'order',
                  label: '委托下单',
                  onClick: onMenuClick,
                },
              ]}
            />
          </Affix>
        </Col>
        <Col span={22} style={{ overflow: 'auto' }}>
        <div ref={contentRef}>
          <div id="account">
            <AccountTable active={activeKey === 'account'} />
          </div>
          <div id="positions">
            <PositionsTable active={activeKey === 'positions'} />
          </div>
          <div id="orders">
            <OrdersTable active={activeKey === 'orders'} />
          </div>
          <div id="trades">
            <TradesTable active={activeKey === 'trades'} />
          </div>
          <div id="order">
            <OrderForm active={activeKey === 'order'} />
          </div>
          </div>
        </Col>
      </Row>
    </div>
    </RefreshProvider>
  );
}

export default App;