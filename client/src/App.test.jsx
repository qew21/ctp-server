import { render, screen } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import App from './App.jsx';

vi.mock('./info/account', () => ({ default: () => <div>Account table</div> }));
vi.mock('./info/positions', () => ({ default: () => <div>Positions table</div> }));
vi.mock('./info/orders', () => ({ default: () => <div>Orders table</div> }));
vi.mock('./info/trades', () => ({ default: () => <div>Trades table</div> }));
vi.mock('./order', () => ({ default: () => <div>Order form</div> }));

test('renders the trading dashboard', () => {
  render(<App />);
  expect(screen.getByText('Account table')).toBeInTheDocument();
  expect(document.title).toBe('CTP Server');
});
