import { useState } from 'react';
import { RefreshContext } from './RefreshContext.js';

export default function RefreshProvider({ children }) {
  const [refreshToken, setRefreshToken] = useState(0);

  const triggerRefresh = () => {
    setRefreshToken((previousToken) => previousToken + 1);
  };

  return (
    <RefreshContext.Provider value={{ triggerRefresh, refreshToken }}>
      {children}
    </RefreshContext.Provider>
  );
}
