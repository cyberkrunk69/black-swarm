import { useState, useEffect, useRef } from 'react';

/**
 * Returns a debounced version of the supplied value.
 * Updates only after `delay` ms have passed without further changes.
 */
export function useDebouncedValue(value, delay = 300) {
    const [debounced, setDebounced] = useState(value);
    const handler = useRef();

    useEffect(() => {
        clearTimeout(handler.current);
        handler.current = setTimeout(() => setDebounced(value), delay);
        return () => clearTimeout(handler.current);
    }, [value, delay]);

    return debounced;
}