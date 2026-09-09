import React, { createContext, useState, useContext } from 'react';

const RefreshContext = createContext();

export const useRefresh = () => useContext(RefreshContext);

export const RefreshProvider = ({ children }) => {
    const [refreshToken, setRefreshToken] = useState(0);

    const triggerRefresh = () => {
        setRefreshToken(prevToken => prevToken + 1);
    };

    return (
        <RefreshContext.Provider value={{ triggerRefresh, refreshToken }}>
            {children}
        </RefreshContext.Provider>
    );
};
