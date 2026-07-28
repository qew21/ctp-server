import { createContext, useContext } from 'react';

export const RefreshContext = createContext();

export const useRefresh = () => useContext(RefreshContext);
